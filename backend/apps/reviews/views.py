from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import structlog

from apps.common.permissions import IsAnalystOrAbove
from apps.organizations.models import User
from .models import ReviewTask
from .serializers import (
    ReviewAssignSerializer,
    ReviewCommentSerializer,
    ReviewDecisionSerializer,
    ReviewTaskSerializer,
)
from .services import ReviewService

logger = structlog.get_logger(__name__)


class ReviewTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReviewTaskSerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["decision", "priority", "assigned_to", "is_suspicious"]
    search_fields = ["comments", "emission_record__source_data"]
    ordering_fields = ["created_at", "due_date", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            ReviewTask.objects.filter(organization=self.request.user.organization)
            .select_related(
                "emission_record",
                "emission_record__upload_session",
                "emission_record__facility",
                "assigned_to",
                "decision_by",
            )
            .prefetch_related("review_comments__author")
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        task = self.get_object()
        serializer = ReviewDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = ReviewService.approve_task(
            task, user=request.user, comments=serializer.validated_data.get("reason", "")
        )
        return Response(ReviewTaskSerializer(updated).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        task = self.get_object()
        serializer = ReviewDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "")
        if not reason:
            return Response(
                {"error": {"code": "reason_required", "message": "Rejection reason is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = ReviewService.reject_task(task, user=request.user, reason=reason)
        return Response(ReviewTaskSerializer(updated).data)

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        task = self.get_object()
        reason = request.data.get("reason", "")
        updated = ReviewService.escalate_task(task, user=request.user, reason=reason)
        return Response(ReviewTaskSerializer(updated).data)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        task = self.get_object()
        serializer = ReviewAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignee = User.objects.get(
                id=serializer.validated_data["assigned_to"],
                organization=request.user.organization,
            )
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "user_not_found", "message": "Assignee not found in this organization."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        updated = ReviewService.assign_task(task, assigned_to=assignee, assigned_by=request.user)
        return Response(ReviewTaskSerializer(updated).data)

    @action(detail=True, methods=["post", "get"], url_path="comments")
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            qs = task.review_comments.select_related("author").order_by("created_at")
            return Response(ReviewCommentSerializer(qs, many=True).data)
        body = request.data.get("body", "").strip()
        if not body:
            return Response(
                {"error": {"code": "body_required", "message": "Comment body is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_internal = request.data.get("is_internal", False)
        comment = ReviewService.add_comment(task, author=request.user, body=body, is_internal=is_internal)
        return Response(ReviewCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
