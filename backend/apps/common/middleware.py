import time
import uuid

import structlog

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        start_time = time.monotonic()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
            user_id=str(request.user.id) if request.user.is_authenticated else "anonymous",
        )

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "http_request",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response["X-Request-ID"] = request_id
        return response


class OrganizationContextMiddleware:
    """
    Attaches the active organization to the request for downstream use.
    Multi-tenancy enforcement: all queries must be scoped to request.organization.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = None

        if request.user.is_authenticated and hasattr(request.user, "organization"):
            request.organization = request.user.organization
            structlog.contextvars.bind_contextvars(
                org_id=str(request.organization.id) if request.organization else None,
                org_slug=request.organization.slug if request.organization else None,
            )

        return self.get_response(request)
