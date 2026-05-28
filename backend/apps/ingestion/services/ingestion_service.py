"""
Core ingestion orchestration service.
Coordinates parsing → validation → normalization → persistence pipeline.
"""
from decimal import Decimal
from typing import List, Optional

import structlog
from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.common.enums import (
    AuditAction,
    DataSourceType,
    EmissionCategory,
    EmissionScope,
    IngestionStatus,
    ValidationStatus,
)
from apps.ingestion.models import RawRecord, UploadSession, ValidationError
from apps.ingestion.services.base_parser import ParsedRow
from apps.ingestion.services.sap_parser import SAPFuelParser
from apps.ingestion.services.travel_parser import CorporateTravelParser
from apps.ingestion.services.utility_parser import UtilityElectricityParser

logger = structlog.get_logger(__name__)

PARSERS = {
    DataSourceType.SAP_FUEL: SAPFuelParser,
    DataSourceType.UTILITY_ELECTRICITY: UtilityElectricityParser,
    DataSourceType.CORPORATE_TRAVEL: CorporateTravelParser,
}


class IngestionService:
    def __init__(self, upload_session: UploadSession):
        self.session = upload_session
        self.organization = upload_session.organization
        self.source_type = upload_session.data_source.source_type

    def run(self) -> UploadSession:
        logger.info(
            "ingestion_start",
            session_id=str(self.session.id),
            source_type=self.source_type,
            file=self.session.original_filename,
        )
        self._mark_processing()

        try:
            file_content = self._read_file()
            parser_class = PARSERS.get(self.source_type)
            if not parser_class:
                raise ValueError(f"No parser registered for source type: {self.source_type}")

            parser = parser_class()
            parsed_rows: List[ParsedRow] = list(parser.parse(file_content))

            self._persist_rows(parsed_rows)
            self._finalize(success=True)

        except Exception as exc:
            logger.error("ingestion_failed", session_id=str(self.session.id), error=str(exc))
            self._finalize(success=False, error_message=str(exc))

        return self.session

    def _read_file(self) -> bytes:
        self.session.file.seek(0)
        return self.session.file.read()

    def _mark_processing(self) -> None:
        self.session.status = IngestionStatus.VALIDATING
        self.session.processing_started_at = timezone.now()
        self.session.save(update_fields=["status", "processing_started_at"])

    @transaction.atomic
    def _persist_rows(self, parsed_rows: List[ParsedRow]) -> None:
        from apps.emissions.models import EmissionRecord

        total = len(parsed_rows)
        passed = failed = warning = 0
        raw_records_to_create = []
        validation_errors_to_create = []

        self.session.total_rows = total
        self.session.save(update_fields=["total_rows"])

        emission_records_batch = []
        raw_record_refs = []

        for parsed in parsed_rows:
            vr = parsed.validation_result
            status = vr.status

            if status == ValidationStatus.PASSED:
                passed += 1
            elif status == ValidationStatus.WARNING:
                warning += 1
            elif status == ValidationStatus.FAILED:
                failed += 1

            normalized = parsed.normalized_data or {}
            anomaly_reasons = normalized.pop("anomaly_reasons", [])
            is_suspicious = len(anomaly_reasons) > 0

            raw = RawRecord(
                upload_session=self.session,
                row_number=parsed.row_number,
                raw_data=parsed.raw_data,
                normalized_data=normalized,
                validation_status=status,
                is_suspicious=is_suspicious,
                suspicion_reasons=anomaly_reasons,
            )
            raw_records_to_create.append(raw)

            for issue in vr.all_issues:
                validation_errors_to_create.append(
                    ValidationError(
                        raw_record=raw,
                        field_name=issue.get("field", ""),
                        error_code=issue.get("code", "UNKNOWN"),
                        message=issue.get("message", ""),
                        severity=ValidationStatus.FAILED if issue in vr.errors else ValidationStatus.WARNING,
                    )
                )

        RawRecord.objects.bulk_create(raw_records_to_create, batch_size=500)

        # Re-query to get PKs, then bulk create ValidationErrors
        created_raws = {r.row_number: r for r in RawRecord.objects.filter(upload_session=self.session)}
        for ve in validation_errors_to_create:
            ve.raw_record = created_raws[ve.raw_record.row_number]

        if validation_errors_to_create:
            ValidationError.objects.bulk_create(validation_errors_to_create, batch_size=1000)

        # Create EmissionRecords for non-failed rows that have co2e data
        for raw in created_raws.values():
            nd = raw.normalized_data or {}
            co2e_str = nd.get("co2e_kg")
            if raw.validation_status != ValidationStatus.FAILED and co2e_str:
                try:
                    co2e = Decimal(co2e_str)
                    emission_records_batch.append(
                        EmissionRecord(
                            organization=self.organization,
                            upload_session=self.session,
                            scope=nd.get("emission_scope", EmissionScope.SCOPE_1),
                            category=nd.get("emission_category", EmissionCategory.STATIONARY_COMBUSTION),
                            co2e_kg=co2e,
                            source_data=nd,
                            status=IngestionStatus.REVIEW_PENDING,
                        )
                    )
                    raw_record_refs.append(raw)
                except Exception:
                    pass

        if emission_records_batch:
            EmissionRecord.objects.bulk_create(emission_records_batch, batch_size=500)
            created_emissions = list(
                EmissionRecord.objects.filter(upload_session=self.session).order_by("created_at")
            )
            for raw, emission in zip(raw_record_refs, created_emissions):
                raw.emission_record = emission

            RawRecord.objects.bulk_update(
                [r for r in raw_record_refs if r.emission_record_id],
                ["emission_record"],
                batch_size=500,
            )

        self.session.processed_rows = total
        self.session.passed_rows = passed
        self.session.failed_rows = failed
        self.session.warning_rows = warning
        self.session.save(update_fields=["processed_rows", "passed_rows", "failed_rows", "warning_rows"])

    def _finalize(self, success: bool, error_message: str = "") -> None:
        self.session.status = IngestionStatus.NORMALIZED if success else IngestionStatus.FAILED
        self.session.processing_completed_at = timezone.now()
        self.session.error_message = error_message
        self.session.save(update_fields=["status", "processing_completed_at", "error_message"])

        AuditService.log(
            action=AuditAction.UPLOAD_CREATED if success else AuditAction.RECORD_CREATED,
            performed_by=self.session.uploaded_by,
            organization=self.organization,
            entity_type="UploadSession",
            entity_id=str(self.session.id),
            description=(
                f"Ingestion of '{self.session.original_filename}' completed. "
                f"Rows: total={self.session.total_rows}, "
                f"passed={self.session.passed_rows}, failed={self.session.failed_rows}."
                if success
                else f"Ingestion of '{self.session.original_filename}' failed: {error_message}"
            ),
            source_file=self.session.original_filename,
        )
        logger.info(
            "ingestion_complete",
            session_id=str(self.session.id),
            success=success,
            total=self.session.total_rows,
            passed=self.session.passed_rows,
            failed=self.session.failed_rows,
        )
