from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import structlog

from apps.audit.services import AuditService
from apps.common.enums import AuditAction, IngestionStatus
from apps.common.permissions import IsAnalystOrAbove, IsDataManagerOrAbove
from apps.common.utils import generate_file_hash
from .models import DataSource, RawRecord, UploadSession
from .serializers import (
    DataSourceSerializer,
    RawRecordSerializer,
    UploadSessionCreateSerializer,
    UploadSessionSerializer,
)
from .tasks import process_upload_session

logger = structlog.get_logger(__name__)


class DataSourceViewSet(viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated, IsDataManagerOrAbove]

    def get_queryset(self):
        return DataSource.objects.filter(organization=self.request.user.organization, is_active=True)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class UploadSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UploadSessionSerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "data_source"]
    search_fields = ["original_filename", "notes"]
    ordering_fields = ["created_at", "status", "total_rows"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            UploadSession.objects.filter(organization=self.request.user.organization)
            .select_related("data_source", "uploaded_by")
        )

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsDataManagerOrAbove],
        parser_classes=[MultiPartParser, FormParser],
        url_path="upload",
    )
    def upload(self, request):
        serializer = UploadSessionCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        data_source = serializer.validated_data["data_source"]
        uploaded_file = serializer.validated_data["file"]
        notes = serializer.validated_data.get("notes", "")

        file_hash = generate_file_hash(uploaded_file)

        # Duplicate file detection
        existing = UploadSession.objects.filter(
            organization=request.user.organization,
            file_hash=file_hash,
        ).first()
        if existing:
            return Response(
                {
                    "error": {
                        "code": "duplicate_file",
                        "message": f"This file was already uploaded on {existing.created_at.date()} (session: {existing.id}).",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        session = UploadSession.objects.create(
            organization=request.user.organization,
            data_source=data_source,
            uploaded_by=request.user,
            original_filename=uploaded_file.name,
            file=uploaded_file,
            file_hash=file_hash,
            file_size_bytes=uploaded_file.size,
            notes=notes,
        )

        AuditService.log(
            action=AuditAction.UPLOAD_CREATED,
            performed_by=request.user,
            organization=request.user.organization,
            entity_type="UploadSession",
            entity_id=str(session.id),
            description=f"File '{uploaded_file.name}' uploaded for source '{data_source.name}'.",
            source_file=uploaded_file.name,
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        task = process_upload_session.delay(str(session.id))
        session.celery_task_id = task.id
        session.save(update_fields=["celery_task_id"])

        return Response(
            UploadSessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="records")
    def records(self, request, pk=None):
        session = self.get_object()
        qs = (
            RawRecord.objects.filter(upload_session=session)
            .prefetch_related("validation_errors")
        )
        validation_status = request.query_params.get("validation_status")
        if validation_status:
            qs = qs.filter(validation_status=validation_status)
        suspicious = request.query_params.get("suspicious")
        if suspicious is not None:
            qs = qs.filter(is_suspicious=suspicious.lower() == "true")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = RawRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(RawRecordSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="reprocess",
            permission_classes=[IsAuthenticated, IsDataManagerOrAbove])
    def reprocess(self, request, pk=None):
        session = self.get_object()
        if session.status == IngestionStatus.LOCKED_FOR_AUDIT:
            return Response(
                {"error": {"code": "session_locked", "message": "This session is locked for audit."}},
                status=status.HTTP_409_CONFLICT,
            )
        from .tasks import reprocess_failed_rows
        task_id = reprocess_failed_rows.delay(str(session.id))
        return Response({"task_id": str(task_id), "message": "Reprocessing queued."})


class SuspiciousRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RawRecordSerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["validation_status", "upload_session"]
    ordering_fields = ["created_at", "row_number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            RawRecord.objects.filter(
                upload_session__organization=self.request.user.organization,
                is_suspicious=True,
            )
            .select_related("upload_session")
            .prefetch_related("validation_errors")
        )
