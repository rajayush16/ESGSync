from django.contrib import admin
from .models import ReviewComment, ReviewTask


@admin.register(ReviewTask)
class ReviewTaskAdmin(admin.ModelAdmin):
    list_display = [
        "id", "decision", "priority", "is_suspicious",
        "assigned_to", "organization", "created_at",
    ]
    list_filter = ["decision", "priority", "is_suspicious"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ["author", "review_task", "is_internal", "created_at"]
    list_filter = ["is_internal"]
    readonly_fields = ["id", "created_at"]
