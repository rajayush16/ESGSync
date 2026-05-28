from django.contrib import admin
from .models import DataSource, RawRecord, UploadSession, ValidationError


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ["name", "source_type", "organization", "is_active", "created_at"]
    list_filter = ["source_type", "is_active", "organization"]
    search_fields = ["name"]


@admin.register(UploadSession)
class UploadSessionAdmin(admin.ModelAdmin):
    list_display = [
        "original_filename", "data_source", "status", "total_rows",
        "passed_rows", "failed_rows", "uploaded_by", "created_at",
    ]
    list_filter = ["status", "data_source__source_type", "organization"]
    search_fields = ["original_filename", "notes"]
    readonly_fields = [
        "id", "file_hash", "file_size_bytes", "processing_started_at",
        "processing_completed_at", "celery_task_id", "created_at",
    ]


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ["row_number", "upload_session", "validation_status", "is_suspicious", "created_at"]
    list_filter = ["validation_status", "is_suspicious"]
    readonly_fields = ["id", "created_at"]


@admin.register(ValidationError)
class ValidationErrorAdmin(admin.ModelAdmin):
    list_display = ["error_code", "field_name", "severity", "message"]
    list_filter = ["severity", "error_code"]
