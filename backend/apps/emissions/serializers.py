from rest_framework import serializers

from apps.common.enums import EmissionScope
from .models import EmissionRecord


class EmissionRecordSerializer(serializers.ModelSerializer):
    scope_display = serializers.CharField(source="get_scope_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    upload_session_filename = serializers.CharField(
        source="upload_session.original_filename", read_only=True
    )
    facility_name = serializers.CharField(source="facility.name", read_only=True, default=None)
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = EmissionRecord
        fields = [
            "id", "scope", "scope_display", "category", "category_display",
            "co2e_kg", "co2e_mt", "status", "status_display",
            "reporting_period_start", "reporting_period_end",
            "facility", "facility_name", "vendor",
            "upload_session", "upload_session_filename",
            "approved_by", "approved_by_name", "approved_at",
            "rejection_reason", "version",
            "source_data", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "co2e_mt", "approved_by", "approved_at", "version",
            "created_at", "updated_at",
        ]


class EmissionSummarySerializer(serializers.Serializer):
    scope = serializers.CharField()
    scope_display = serializers.CharField()
    total_co2e_kg = serializers.DecimalField(max_digits=20, decimal_places=3)
    total_co2e_mt = serializers.DecimalField(max_digits=20, decimal_places=6)
    record_count = serializers.IntegerField()


class EmissionsByPeriodSerializer(serializers.Serializer):
    period = serializers.CharField()
    scope_1_co2e_kg = serializers.DecimalField(max_digits=20, decimal_places=3)
    scope_2_co2e_kg = serializers.DecimalField(max_digits=20, decimal_places=3)
    scope_3_co2e_kg = serializers.DecimalField(max_digits=20, decimal_places=3)
    total_co2e_kg = serializers.DecimalField(max_digits=20, decimal_places=3)
