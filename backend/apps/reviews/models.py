from django.db import models

from apps.common.enums import ReviewDecision
from apps.common.models import BaseModel


class ReviewTask(BaseModel):
    """
    An analyst review task associated with a specific EmissionRecord.
    Created automatically when records reach REVIEW_PENDING status.
    """

    emission_record = models.ForeignKey(
        "emissions.EmissionRecord",
        on_delete=models.CASCADE,
        related_name="review_tasks",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="review_tasks",
    )
    assigned_to = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reviews",
    )
    assigned_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delegated_reviews",
    )
    decision = models.CharField(
        max_length=20,
        choices=ReviewDecision.choices,
        default=ReviewDecision.PENDING,
        db_index=True,
    )
    decision_at = models.DateTimeField(null=True, blank=True)
    decision_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_reviews",
    )
    comments = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("URGENT", "Urgent")],
        default="MEDIUM",
    )
    due_date = models.DateField(null=True, blank=True)
    is_suspicious = models.BooleanField(default=False)

    class Meta:
        db_table = "review_tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "decision"]),
            models.Index(fields=["assigned_to", "decision"]),
            models.Index(fields=["is_suspicious", "decision"]),
        ]

    def __str__(self):
        return f"ReviewTask[{self.decision}] → {self.emission_record_id}"

    @property
    def is_pending(self) -> bool:
        return self.decision == ReviewDecision.PENDING

    @property
    def is_closed(self) -> bool:
        return self.decision in {ReviewDecision.APPROVED, ReviewDecision.REJECTED}


class ReviewComment(BaseModel):
    review_task = models.ForeignKey(
        ReviewTask,
        on_delete=models.CASCADE,
        related_name="review_comments",
    )
    author = models.ForeignKey(
        "organizations.User",
        on_delete=models.PROTECT,
        related_name="review_comments",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=False)

    class Meta:
        db_table = "review_comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author_id} on task {self.review_task_id}"
