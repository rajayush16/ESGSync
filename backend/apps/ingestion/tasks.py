import structlog
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
structlog_logger = structlog.get_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="ingestion.process_upload_session",
)
def process_upload_session(self, upload_session_id: str) -> dict:
    from apps.ingestion.models import UploadSession
    from apps.ingestion.services.ingestion_service import IngestionService

    try:
        session = UploadSession.objects.select_related(
            "organization", "data_source", "uploaded_by"
        ).get(id=upload_session_id)
    except UploadSession.DoesNotExist:
        logger.error(f"UploadSession {upload_session_id} not found.")
        return {"error": "session_not_found"}

    session.celery_task_id = self.request.id
    session.save(update_fields=["celery_task_id"])

    structlog_logger.info(
        "task_start",
        task_id=self.request.id,
        session_id=upload_session_id,
    )

    try:
        service = IngestionService(session)
        session = service.run()
        return {
            "session_id": str(session.id),
            "status": session.status,
            "total_rows": session.total_rows,
            "passed_rows": session.passed_rows,
            "failed_rows": session.failed_rows,
        }
    except Exception as exc:
        structlog_logger.error("task_failed", session_id=upload_session_id, error=str(exc))
        raise self.retry(exc=exc)


@shared_task(name="ingestion.reprocess_failed_rows")
def reprocess_failed_rows(upload_session_id: str) -> dict:
    """Re-run ingestion for a session that has already been processed, typically after data corrections."""
    from apps.ingestion.models import UploadSession, RawRecord
    from apps.common.enums import IngestionStatus

    try:
        session = UploadSession.objects.get(id=upload_session_id)
    except UploadSession.DoesNotExist:
        return {"error": "session_not_found"}

    RawRecord.objects.filter(upload_session=session).delete()
    session.status = IngestionStatus.UPLOADED
    session.processed_rows = 0
    session.passed_rows = 0
    session.failed_rows = 0
    session.warning_rows = 0
    session.error_message = ""
    session.save()

    return process_upload_session.delay(upload_session_id).id
