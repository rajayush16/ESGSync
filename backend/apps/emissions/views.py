from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import structlog

from apps.common.permissions import IsAnalystOrAbove, IsAuditorOrAbove
from .models import EmissionRecord
from .serializers import EmissionRecordSerializer, EmissionSummarySerializer
from .services import EmissionRecordService

logger = structlog.get_logger(__name__)


class EmissionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmissionRecordSerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["scope", "category", "status", "facility", "upload_session"]
    search_fields = ["source_data"]
    ordering_fields = ["created_at", "co2e_kg", "co2e_mt", "reporting_period_start"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            EmissionRecord.objects.filter(organization=self.request.user.organization)
            .select_related("upload_session", "facility", "approved_by")
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        data = EmissionRecordService.get_scope_summary(request.user.organization)
        serializer = EmissionSummarySerializer(data, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAnalystOrAbove],
    )
    def approve(self, request, pk=None):
        record = self.get_object()
        updated = EmissionRecordService.approve(record, user=request.user)
        return Response(EmissionRecordSerializer(updated).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAnalystOrAbove],
    )
    def reject(self, request, pk=None):
        record = self.get_object()
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"error": {"code": "reason_required", "message": "Rejection reason is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = EmissionRecordService.reject(record, user=request.user, reason=reason)
        return Response(EmissionRecordSerializer(updated).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="lock-for-audit",
        permission_classes=[IsAuthenticated, IsAuditorOrAbove],
    )
    def lock_for_audit(self, request, pk=None):
        record = self.get_object()
        updated = EmissionRecordService.lock_for_audit(record, user=request.user)
        return Response(EmissionRecordSerializer(updated).data)
