from decimal import Decimal

from django.db import models

from apps.common.enums import EmissionCategory, EmissionScope, IngestionStatus
from apps.common.models import BaseModel


class EmissionRecord(BaseModel):
    """
    Canonical emission record — the normalized, calculable unit of ESG data.
    Each record maps to one RawRecord row after successful ingestion.
    Records become immutable once LOCKED_FOR_AUDIT.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="emission_records",
        db_index=True,
    )
    upload_session = models.ForeignKey(
        "ingestion.UploadSession",
        on_delete=models.PROTECT,
        related_name="emission_records",
        db_index=True,
    )
    scope = models.CharField(
        max_length=20,
        choices=EmissionScope.choices,
        db_index=True,
    )
    category = models.CharField(
        max_length=50,
        choices=EmissionCategory.choices,
        db_index=True,
    )
    co2e_kg = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Total CO₂e in kilograms",
    )
    co2e_mt = models.DecimalField(
        max_digits=20,
        decimal_places=9,
        null=True,
        blank=True,
        help_text="Total CO₂e in metric tons (auto-calculated)",
    )
    source_data = models.JSONField(default=dict, help_text="Normalized source data snapshot")
    status = models.CharField(
        max_length=30,
        choices=IngestionStatus.choices,
        default=IngestionStatus.REVIEW_PENDING,
        db_index=True,
    )
    reporting_period_start = models.DateField(null=True, blank=True, db_index=True)
    reporting_period_end = models.DateField(null=True, blank=True)
    facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emission_records",
    )
    vendor = models.ForeignKey(
        "organizations.Vendor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emission_records",
    )
    approved_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_emissions",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "emission_records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "scope", "-created_at"]),
            models.Index(fields=["organization", "category", "-created_at"]),
            models.Index(fields=["status", "organization"]),
            models.Index(fields=["organization", "reporting_period_start"]),
        ]

    def save(self, *args, **kwargs):
        if self.co2e_kg is not None:
            self.co2e_mt = self.co2e_kg / Decimal("1000")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.scope} — {self.co2e_kg} kg CO₂e [{self.status}]"

    @property
    def is_locked(self) -> bool:
        return self.status == IngestionStatus.LOCKED_FOR_AUDIT

    @property
    def is_approved(self) -> bool:
        return self.status == IngestionStatus.APPROVED
