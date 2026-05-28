import os

from django.db import models

from apps.common.enums import DataSourceType, IngestionStatus, ValidationStatus
from apps.common.models import BaseModel


def upload_session_file_path(instance, filename):
    org_slug = instance.organization.slug
    return f"uploads/{org_slug}/{instance.id}/{filename}"


class DataSource(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="data_sources",
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=DataSourceType.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)

    class Meta:
        db_table = "data_sources"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class UploadSession(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="upload_sessions",
    )
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name="upload_sessions",
    )
    uploaded_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.PROTECT,
        related_name="upload_sessions",
    )
    original_filename = models.CharField(max_length=500)
    file = models.FileField(upload_to=upload_session_file_path, max_length=1000)
    file_hash = models.CharField(max_length=64, db_index=True)
    file_size_bytes = models.BigIntegerField(default=0)
    status = models.CharField(
        max_length=30,
        choices=IngestionStatus.choices,
        default=IngestionStatus.UPLOADED,
        db_index=True,
    )
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    passed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    warning_rows = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "upload_sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["status", "organization"]),
            models.Index(fields=["file_hash"]),
        ]

    def __str__(self):
        return f"{self.original_filename} [{self.status}]"

    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round(self.passed_rows / self.total_rows * 100, 1)

    @property
    def file_size_mb(self) -> float:
        return round(self.file_size_bytes / (1024 * 1024), 2)


class RawRecord(BaseModel):
    upload_session = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name="raw_records",
    )
    row_number = models.IntegerField()
    raw_data = models.JSONField()
    normalized_data = models.JSONField(null=True, blank=True)
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
        db_index=True,
    )
    is_suspicious = models.BooleanField(default=False, db_index=True)
    suspicion_reasons = models.JSONField(default=list)
    processing_notes = models.TextField(blank=True)
    emission_record = models.OneToOneField(
        "emissions.EmissionRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_record",
    )

    class Meta:
        db_table = "raw_records"
        unique_together = [("upload_session", "row_number")]
        ordering = ["row_number"]
        indexes = [
            models.Index(fields=["upload_session", "validation_status"]),
            models.Index(fields=["upload_session", "is_suspicious"]),
        ]

    def __str__(self):
        return f"Row {self.row_number} of {self.upload_session_id}"


class ValidationError(BaseModel):
    raw_record = models.ForeignKey(
        RawRecord,
        on_delete=models.CASCADE,
        related_name="validation_errors",
    )
    field_name = models.CharField(max_length=100, blank=True)
    error_code = models.CharField(max_length=100)
    message = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.FAILED,
    )

    class Meta:
        db_table = "validation_errors"
        ordering = ["severity", "field_name"]
        indexes = [
            models.Index(fields=["raw_record", "severity"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.error_code}: {self.message[:60]}"
