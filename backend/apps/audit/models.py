from django.db import models

from apps.common.enums import AuditAction
from apps.common.models import UUIDModel, TimeStampedModel


class AuditLog(UUIDModel, TimeStampedModel):
    """
    Immutable audit log. No update or delete methods — enforced at DB level via trigger
    and at app level by never calling save() after creation.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="audit_logs",
        null=True,
        blank=True,
        db_index=True,
    )
    performed_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=AuditAction.choices, db_index=True)
    entity_type = models.CharField(max_length=100, blank=True, db_index=True)
    entity_id = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField(blank=True)
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    source_file = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["performed_by", "-created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RuntimeError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("AuditLog records are immutable and cannot be deleted.")

    def __str__(self):
        return f"[{self.action}] {self.entity_type}:{self.entity_id} by {self.performed_by_id}"
