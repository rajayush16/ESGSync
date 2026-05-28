from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(
        source="performed_by.get_full_name", read_only=True, default=None
    )
    performed_by_email = serializers.CharField(
        source="performed_by.email", read_only=True, default=None
    )

    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "entity_type", "entity_id", "description",
            "previous_value", "new_value", "metadata",
            "performed_by", "performed_by_name", "performed_by_email",
            "ip_address", "source_file", "created_at",
        ]
        read_only_fields = fields
