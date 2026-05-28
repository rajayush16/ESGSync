from rest_framework import serializers

from apps.emissions.serializers import EmissionRecordSerializer
from .models import ReviewComment, ReviewTask


class ReviewCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = ReviewComment
        fields = ["id", "author", "author_name", "body", "is_internal", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class ReviewTaskSerializer(serializers.ModelSerializer):
    emission_record_detail = EmissionRecordSerializer(source="emission_record", read_only=True)
    assigned_to_name = serializers.CharField(
        source="assigned_to.get_full_name", read_only=True, default=None
    )
    decision_by_name = serializers.CharField(
        source="decision_by.get_full_name", read_only=True, default=None
    )
    comments_list = ReviewCommentSerializer(source="review_comments", many=True, read_only=True)

    class Meta:
        model = ReviewTask
        fields = [
            "id", "emission_record", "emission_record_detail",
            "decision", "decision_at", "decision_by", "decision_by_name",
            "assigned_to", "assigned_to_name",
            "comments", "comments_list",
            "priority", "due_date", "is_suspicious",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "decision_at", "created_at", "updated_at"]


class ReviewDecisionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class ReviewAssignSerializer(serializers.Serializer):
    assigned_to = serializers.UUIDField()
