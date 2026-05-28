from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
import structlog

logger = structlog.get_logger(__name__)


class ESGSyncException(Exception):
    default_message = "An unexpected error occurred."
    default_code = "internal_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message=None, code=None, extra=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.extra = extra or {}
        super().__init__(self.message)


class ValidationException(ESGSyncException):
    default_message = "Data validation failed."
    default_code = "validation_error"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class IngestionException(ESGSyncException):
    default_message = "Data ingestion failed."
    default_code = "ingestion_error"
    status_code = status.HTTP_400_BAD_REQUEST


class OrganizationException(ESGSyncException):
    default_message = "Organization operation failed."
    default_code = "organization_error"
    status_code = status.HTTP_400_BAD_REQUEST


class PermissionDeniedException(ESGSyncException):
    default_message = "You do not have permission to perform this action."
    default_code = "permission_denied"
    status_code = status.HTTP_403_FORBIDDEN


class RecordLockedException(ESGSyncException):
    default_message = "This record is locked for audit and cannot be modified."
    default_code = "record_locked"
    status_code = status.HTTP_409_CONFLICT


class InvalidWorkflowTransitionException(ESGSyncException):
    default_message = "This workflow transition is not permitted."
    default_code = "invalid_transition"
    status_code = status.HTTP_409_CONFLICT


class FileUploadException(ESGSyncException):
    default_message = "File upload failed."
    default_code = "upload_error"
    status_code = status.HTTP_400_BAD_REQUEST


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, ESGSyncException):
        logger.warning(
            "application_exception",
            code=exc.code,
            message=exc.message,
            extra=exc.extra,
            view=context.get("view").__class__.__name__ if context.get("view") else None,
        )
        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.extra,
                }
            },
            status=exc.status_code,
        )

    if response is not None:
        error_data = {
            "error": {
                "code": "request_error",
                "message": "Request processing failed.",
                "details": response.data,
            }
        }
        response.data = error_data
        return response

    logger.error(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
    )
    return Response(
        {
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
