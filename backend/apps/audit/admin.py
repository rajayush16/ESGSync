from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "entity_type", "entity_id", "performed_by", "organization", "created_at"]
    list_filter = ["action", "entity_type", "organization"]
    search_fields = ["description", "entity_id"]
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
