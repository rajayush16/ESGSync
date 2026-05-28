from typing import Any, Optional

import structlog

from apps.common.enums import AuditAction
from .models import AuditLog

logger = structlog.get_logger(__name__)


class AuditService:
    @staticmethod
    def log(
        action: AuditAction,
        performed_by=None,
        organization=None,
        entity_type: str = "",
        entity_id: str = "",
        description: str = "",
        previous_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        source_file: str = "",
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            performed_by=performed_by,
            organization=organization,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else "",
            description=description,
            previous_value=previous_value,
            new_value=new_value,
            metadata=metadata or {},
            ip_address=ip_address,
            source_file=source_file,
        )
        entry.save()
        logger.debug(
            "audit_log_created",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
        )
        return entry

    @staticmethod
    def log_field_change(
        entity,
        field_name: str,
        old_value: Any,
        new_value: Any,
        performed_by=None,
        organization=None,
    ) -> AuditLog:
        entity_type = entity.__class__.__name__
        return AuditService.log(
            action=AuditAction.RECORD_UPDATED,
            performed_by=performed_by,
            organization=organization,
            entity_type=entity_type,
            entity_id=str(entity.pk),
            description=f"{entity_type}.{field_name} changed.",
            previous_value={field_name: str(old_value)},
            new_value={field_name: str(new_value)},
        )

    @staticmethod
    def get_entity_history(entity_type: str, entity_id: str):
        return AuditLog.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
        ).select_related("performed_by").order_by("-created_at")
