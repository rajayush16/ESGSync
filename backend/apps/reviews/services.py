from django.utils import timezone
import structlog

from apps.audit.services import AuditService
from apps.common.enums import AuditAction, IngestionStatus, ReviewDecision
from apps.common.exceptions import InvalidWorkflowTransitionException, PermissionDeniedException
from apps.emissions.services import EmissionRecordService
from .models import ReviewComment, ReviewTask

logger = structlog.get_logger(__name__)


class ReviewService:
    @staticmethod
    def create_task_for_record(emission_record, assigned_to=None, priority="MEDIUM") -> ReviewTask:
        existing = ReviewTask.objects.filter(
            emission_record=emission_record,
            decision=ReviewDecision.PENDING,
        ).first()
        if existing:
            return existing

        task = ReviewTask.objects.create(
            emission_record=emission_record,
            organization=emission_record.organization,
            assigned_to=assigned_to,
            priority=priority,
            is_suspicious=bool(
                getattr(emission_record, "raw_record", None)
                and emission_record.raw_record.is_suspicious
            ),
        )
        logger.info(
            "review_task_created",
            task_id=str(task.id),
            record_id=str(emission_record.id),
            assigned_to=str(assigned_to.id) if assigned_to else None,
        )
        return task

    @staticmethod
    def assign_task(task: ReviewTask, assigned_to, assigned_by) -> ReviewTask:
        if task.is_closed:
            raise InvalidWorkflowTransitionException("Cannot reassign a closed review task.")
        task.assigned_to = assigned_to
        task.assigned_by = assigned_by
        task.save(update_fields=["assigned_to", "assigned_by", "updated_at"])

        AuditService.log(
            action=AuditAction.REVIEW_ASSIGNED,
            performed_by=assigned_by,
            organization=task.organization,
            entity_type="ReviewTask",
            entity_id=str(task.id),
            description=f"Task assigned to {assigned_to.email} by {assigned_by.email}.",
        )
        return task

    @staticmethod
    def approve_task(task: ReviewTask, user, comments: str = "") -> ReviewTask:
        if task.is_closed:
            raise InvalidWorkflowTransitionException("This review task is already closed.")
        if task.assigned_to and task.assigned_to != user and not user.can_manage_uploads():
            raise PermissionDeniedException("Only the assigned analyst or a manager can approve.")

        task.decision = ReviewDecision.APPROVED
        task.decision_at = timezone.now()
        task.decision_by = user
        task.comments = comments
        task.save(update_fields=["decision", "decision_at", "decision_by", "comments", "updated_at"])

        EmissionRecordService.approve(task.emission_record, user=user)

        AuditService.log(
            action=AuditAction.RECORD_APPROVED,
            performed_by=user,
            organization=task.organization,
            entity_type="ReviewTask",
            entity_id=str(task.id),
            description=f"Review task approved by {user.email}.",
        )
        return task

    @staticmethod
    def reject_task(task: ReviewTask, user, reason: str) -> ReviewTask:
        if not reason or not reason.strip():
            raise ValueError("Rejection reason is required.")
        if task.is_closed:
            raise InvalidWorkflowTransitionException("This review task is already closed.")

        task.decision = ReviewDecision.REJECTED
        task.decision_at = timezone.now()
        task.decision_by = user
        task.comments = reason.strip()
        task.save(update_fields=["decision", "decision_at", "decision_by", "comments", "updated_at"])

        EmissionRecordService.reject(task.emission_record, user=user, reason=reason)

        AuditService.log(
            action=AuditAction.RECORD_REJECTED,
            performed_by=user,
            organization=task.organization,
            entity_type="ReviewTask",
            entity_id=str(task.id),
            description=f"Review task rejected by {user.email}. Reason: {reason}",
        )
        return task

    @staticmethod
    def escalate_task(task: ReviewTask, user, reason: str = "") -> ReviewTask:
        if task.is_closed:
            raise InvalidWorkflowTransitionException("Cannot escalate a closed task.")
        task.decision = ReviewDecision.ESCALATED
        task.comments = reason
        task.save(update_fields=["decision", "comments", "updated_at"])

        AuditService.log(
            action=AuditAction.RECORD_ESCALATED,
            performed_by=user,
            organization=task.organization,
            entity_type="ReviewTask",
            entity_id=str(task.id),
            description=f"Review task escalated by {user.email}.",
        )
        return task

    @staticmethod
    def add_comment(task: ReviewTask, author, body: str, is_internal: bool = False) -> ReviewComment:
        comment = ReviewComment.objects.create(
            review_task=task,
            author=author,
            body=body.strip(),
            is_internal=is_internal,
        )
        return comment
