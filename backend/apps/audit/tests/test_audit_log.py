import pytest

from apps.common.enums import AuditAction
from apps.audit.models import AuditLog
from apps.audit.services import AuditService


@pytest.mark.django_db
class TestAuditLogImmutability:
    def test_audit_log_create(self):
        log = AuditLog(
            action=AuditAction.USER_LOGIN,
            description="Test login",
        )
        log.save()
        assert log.pk is not None

    def test_audit_log_cannot_be_updated(self):
        log = AuditLog(
            action=AuditAction.USER_LOGIN,
            description="Test",
        )
        log.save()
        with pytest.raises(RuntimeError, match="immutable"):
            log.description = "Modified"
            log.save()

    def test_audit_log_cannot_be_deleted(self):
        log = AuditLog(
            action=AuditAction.USER_LOGIN,
            description="Test",
        )
        log.save()
        with pytest.raises(RuntimeError, match="immutable"):
            log.delete()

    def test_audit_service_log(self):
        log = AuditService.log(
            action=AuditAction.UPLOAD_CREATED,
            entity_type="UploadSession",
            entity_id="test-id-123",
            description="Test upload",
        )
        assert log.pk is not None
        assert log.action == AuditAction.UPLOAD_CREATED
        assert log.entity_id == "test-id-123"

    def test_entity_history_retrieval(self):
        AuditService.log(action=AuditAction.RECORD_CREATED, entity_type="EmissionRecord", entity_id="abc-1")
        AuditService.log(action=AuditAction.RECORD_UPDATED, entity_type="EmissionRecord", entity_id="abc-1")
        AuditService.log(action=AuditAction.RECORD_APPROVED, entity_type="EmissionRecord", entity_id="abc-1")

        history = AuditService.get_entity_history("EmissionRecord", "abc-1")
        assert history.count() == 3
