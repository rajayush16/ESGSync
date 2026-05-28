from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Avg, Count, Sum, Q
from django.db.models.functions import TruncMonth, TruncYear

import structlog

from apps.common.enums import EmissionScope, IngestionStatus, ValidationStatus
from apps.emissions.models import EmissionRecord
from apps.ingestion.models import UploadSession, RawRecord

logger = structlog.get_logger(__name__)


class DashboardAnalyticsService:
    @staticmethod
    def get_overview(organization) -> Dict[str, Any]:
        approved_statuses = [IngestionStatus.APPROVED, IngestionStatus.LOCKED_FOR_AUDIT]

        total_co2e = (
            EmissionRecord.objects.filter(
                organization=organization, status__in=approved_statuses
            ).aggregate(total=Sum("co2e_kg"))["total"]
            or Decimal("0")
        )

        scope_breakdown = {}
        for scope in EmissionScope:
            val = (
                EmissionRecord.objects.filter(
                    organization=organization,
                    status__in=approved_statuses,
                    scope=scope,
                ).aggregate(total=Sum("co2e_kg"))["total"]
                or Decimal("0")
            )
            scope_breakdown[scope.value] = float(val)

        pending_review_count = EmissionRecord.objects.filter(
            organization=organization,
            status=IngestionStatus.REVIEW_PENDING,
        ).count()

        suspicious_count = RawRecord.objects.filter(
            upload_session__organization=organization,
            is_suspicious=True,
        ).count()

        failed_records = RawRecord.objects.filter(
            upload_session__organization=organization,
            validation_status=ValidationStatus.FAILED,
        ).count()

        recent_uploads = (
            UploadSession.objects.filter(organization=organization)
            .order_by("-created_at")[:5]
            .values("id", "original_filename", "status", "total_rows", "created_at")
        )

        return {
            "total_co2e_kg": float(total_co2e),
            "total_co2e_mt": float(total_co2e / Decimal("1000")),
            "scope_breakdown_kg": scope_breakdown,
            "pending_review_count": pending_review_count,
            "suspicious_record_count": suspicious_count,
            "failed_validation_count": failed_records,
            "recent_uploads": list(recent_uploads),
        }

    @staticmethod
    def get_emissions_by_month(
        organization,
        year: Optional[int] = None,
        scope: Optional[str] = None,
    ) -> List[Dict]:
        qs = EmissionRecord.objects.filter(
            organization=organization,
            status__in=[IngestionStatus.APPROVED, IngestionStatus.LOCKED_FOR_AUDIT],
            reporting_period_start__isnull=False,
        )
        if year:
            qs = qs.filter(reporting_period_start__year=year)
        if scope:
            qs = qs.filter(scope=scope)

        results = (
            qs.annotate(month=TruncMonth("reporting_period_start"))
            .values("month", "scope")
            .annotate(total_co2e_kg=Sum("co2e_kg"))
            .order_by("month", "scope")
        )

        monthly: Dict[str, Dict] = {}
        for row in results:
            key = row["month"].strftime("%Y-%m") if row["month"] else "unknown"
            if key not in monthly:
                monthly[key] = {
                    "period": key,
                    "scope_1_co2e_kg": Decimal("0"),
                    "scope_2_co2e_kg": Decimal("0"),
                    "scope_3_co2e_kg": Decimal("0"),
                }
            scope_key = f"{row['scope'].lower()}_co2e_kg"
            monthly[key][scope_key] = row["total_co2e_kg"] or Decimal("0")

        for m in monthly.values():
            m["total_co2e_kg"] = m["scope_1_co2e_kg"] + m["scope_2_co2e_kg"] + m["scope_3_co2e_kg"]

        return sorted(monthly.values(), key=lambda x: x["period"])

    @staticmethod
    def get_upload_stats(organization) -> Dict[str, Any]:
        total_sessions = UploadSession.objects.filter(organization=organization).count()
        by_status = (
            UploadSession.objects.filter(organization=organization)
            .values("status")
            .annotate(count=Count("id"))
        )
        by_source = (
            UploadSession.objects.filter(organization=organization)
            .values("data_source__source_type", "data_source__name")
            .annotate(count=Count("id"), total_rows=Sum("total_rows"))
            .order_by("-count")
        )
        return {
            "total_sessions": total_sessions,
            "by_status": {r["status"]: r["count"] for r in by_status},
            "by_source": list(by_source),
        }

    @staticmethod
    def get_suspicious_summary(organization) -> Dict[str, Any]:
        total = RawRecord.objects.filter(
            upload_session__organization=organization,
            is_suspicious=True,
        ).count()
        by_source = (
            RawRecord.objects.filter(
                upload_session__organization=organization,
                is_suspicious=True,
            )
            .values("upload_session__data_source__source_type")
            .annotate(count=Count("id"))
        )
        return {
            "total_suspicious": total,
            "by_source_type": {r["upload_session__data_source__source_type"]: r["count"] for r in by_source},
        }
