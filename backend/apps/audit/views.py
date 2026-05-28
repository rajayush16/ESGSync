from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsAnalystOrAbove, IsAuditorOrAbove
from .models import AuditLog
from .serializers import AuditLogSerializer
from .services import AuditService


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["action", "entity_type", "performed_by"]
    search_fields = ["description", "entity_id", "entity_type"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            AuditLog.objects.filter(organization=self.request.user.organization)
            .select_related("performed_by")
        )

    @action(detail=False, methods=["get"], url_path="entity/(?P<entity_type>[^/.]+)/(?P<entity_id>[^/.]+)")
    def entity_history(self, request, entity_type=None, entity_id=None):
        logs = AuditService.get_entity_history(entity_type, entity_id)
        logs = logs.filter(organization=request.user.organization)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
