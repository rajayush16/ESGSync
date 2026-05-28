from decimal import Decimal
from typing import Dict, List

from django.db.models import QuerySet, Sum
from django.utils import timezone

import structlog

from apps.audit.services import AuditService
from apps.common.enums import AuditAction, EmissionScope, IngestionStatus
from apps.common.exceptions import RecordLockedException, InvalidWorkflowTransitionException
from .models import EmissionRecord

logger = structlog.get_logger(__name__)

VALID_TRANSITIONS = {
    IngestionStatus.REVIEW_PENDING: {IngestionStatus.APPROVED, IngestionStatus.REJECTED},
    IngestionStatus.APPROVED: {IngestionStatus.LOCKED_FOR_AUDIT},
    IngestionStatus.REJECTED: {IngestionStatus.REVIEW_PENDING},
    IngestionStatus.LOCKED_FOR_AUDIT: set(),
}


class EmissionRecordService:
    @staticmethod
    def approve(record: EmissionRecord, user, reason: str = "") -> EmissionRecord:
        EmissionRecordService._assert_not_locked(record)
        EmissionRecordService._assert_valid_transition(record, IngestionStatus.APPROVED)

        previous_status = record.status
        record.status = IngestionStatus.APPROVED
        record.approved_by = user
        record.approved_at = timezone.now()
        record.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

        AuditService.log(
            action=AuditAction.RECORD_APPROVED,
            performed_by=user,
            organization=record.organization,
            entity_type="EmissionRecord",
            entity_id=str(record.id),
            description=f"Record approved by {user.email}.",
            previous_value={"status": previous_status},
            new_value={"status": IngestionStatus.APPROVED},
        )
        return record

    @staticmethod
    def reject(record: EmissionRecord, user, reason: str) -> EmissionRecord:
        if not reason or not reason.strip():
            raise ValueError("Rejection reason is required.")
        EmissionRecordService._assert_not_locked(record)
        EmissionRecordService._assert_valid_transition(record, IngestionStatus.REJECTED)

        previous_status = record.status
        record.status = IngestionStatus.REJECTED
        record.rejection_reason = reason.strip()
        record.save(update_fields=["status", "rejection_reason", "updated_at"])

        AuditService.log(
            action=AuditAction.RECORD_REJECTED,
            performed_by=user,
            organization=record.organization,
            entity_type="EmissionRecord",
            entity_id=str(record.id),
            description=f"Record rejected by {user.email}. Reason: {reason}",
            previous_value={"status": previous_status},
            new_value={"status": IngestionStatus.REJECTED, "rejection_reason": reason},
        )
        return record

    @staticmethod
    def lock_for_audit(record: EmissionRecord, user) -> EmissionRecord:
        EmissionRecordService._assert_valid_transition(record, IngestionStatus.LOCKED_FOR_AUDIT)

        previous_status = record.status
        record.status = IngestionStatus.LOCKED_FOR_AUDIT
        record.save(update_fields=["status", "updated_at"])

        AuditService.log(
            action=AuditAction.RECORD_LOCKED,
            performed_by=user,
            organization=record.organization,
            entity_type="EmissionRecord",
            entity_id=str(record.id),
            description=f"Record locked for audit by {user.email}.",
            previous_value={"status": previous_status},
            new_value={"status": IngestionStatus.LOCKED_FOR_AUDIT},
        )
        return record

    @staticmethod
    def get_scope_summary(organization) -> List[Dict]:
        from django.db.models import Count
        results = (
            EmissionRecord.objects.filter(
                organization=organization,
                status__in=[IngestionStatus.APPROVED, IngestionStatus.LOCKED_FOR_AUDIT],
            )
            .values("scope")
            .annotate(
                total_co2e_kg=Sum("co2e_kg"),
                record_count=Count("id"),
            )
            .order_by("scope")
        )
        scope_map = {s.value: s.label for s in EmissionScope}
        return [
            {
                "scope": r["scope"],
                "scope_display": scope_map.get(r["scope"], r["scope"]),
                "total_co2e_kg": r["total_co2e_kg"] or Decimal("0"),
                "total_co2e_mt": (r["total_co2e_kg"] or Decimal("0")) / Decimal("1000"),
                "record_count": r["record_count"],
            }
            for r in results
        ]

    @staticmethod
    def _assert_not_locked(record: EmissionRecord) -> None:
        if record.is_locked:
            raise RecordLockedException(
                f"EmissionRecord {record.id} is locked for audit and cannot be modified."
            )

    @staticmethod
    def _assert_valid_transition(record: EmissionRecord, target_status: str) -> None:
        allowed = VALID_TRANSITIONS.get(record.status, set())
        if target_status not in allowed:
            raise InvalidWorkflowTransitionException(
                f"Cannot transition from '{record.status}' to '{target_status}'. "
                f"Allowed transitions: {allowed or 'none'}."
            )
