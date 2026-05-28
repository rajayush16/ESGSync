from django.contrib import admin
from .models import EmissionRecord


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = [
        "id", "scope", "category", "co2e_kg", "status",
        "organization", "upload_session", "created_at",
    ]
    list_filter = ["scope", "category", "status", "organization"]
    readonly_fields = ["id", "co2e_mt", "created_at", "updated_at"]
    search_fields = ["source_data"]
