from rest_framework import serializers

from apps.common.enums import DataSourceType
from .models import DataSource, RawRecord, UploadSession, ValidationError


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ["id", "name", "source_type", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class ValidationErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationError
        fields = ["id", "field_name", "error_code", "message", "severity"]


class RawRecordSerializer(serializers.ModelSerializer):
    validation_errors = ValidationErrorSerializer(many=True, read_only=True)

    class Meta:
        model = RawRecord
        fields = [
            "id", "row_number", "raw_data", "normalized_data",
            "validation_status", "is_suspicious", "suspicion_reasons",
            "processing_notes", "validation_errors", "created_at",
        ]
        read_only_fields = fields


class UploadSessionSerializer(serializers.ModelSerializer):
    data_source_name = serializers.CharField(source="data_source.name", read_only=True)
    data_source_type = serializers.CharField(source="data_source.source_type", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.get_full_name", read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)

    class Meta:
        model = UploadSession
        fields = [
            "id", "original_filename", "file_size_mb", "status",
            "data_source", "data_source_name", "data_source_type",
            "uploaded_by", "uploaded_by_name",
            "total_rows", "processed_rows", "passed_rows",
            "failed_rows", "warning_rows", "success_rate",
            "error_message", "notes",
            "processing_started_at", "processing_completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id", "file_size_mb", "status", "uploaded_by",
            "total_rows", "processed_rows", "passed_rows",
            "failed_rows", "warning_rows", "success_rate",
            "error_message", "processing_started_at",
            "processing_completed_at", "created_at",
        ]


class UploadSessionCreateSerializer(serializers.Serializer):
    data_source = serializers.PrimaryKeyRelatedField(queryset=DataSource.objects.none())
    file = serializers.FileField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated and request.user.organization:
            self.fields["data_source"].queryset = DataSource.objects.filter(
                organization=request.user.organization,
                is_active=True,
            )

    def validate_file(self, value):
        allowed_extensions = [".csv", ".xlsx", ".xls"]
        name = value.name.lower()
        if not any(name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError("File exceeds the 100MB size limit.")
        return value
