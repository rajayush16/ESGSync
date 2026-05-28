from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Facility, Organization, User, Vendor


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "industry_sector", "country", "is_active", "created_at"]
    list_filter = ["is_active", "industry_sector"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "get_full_name", "organization", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "organization"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login_ip"]
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Organization", {"fields": ("organization", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Metadata", {"fields": ("created_at", "updated_at", "last_login_ip")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "organization", "role"),
        }),
    )
    ordering = ["email"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "organization", "country", "is_active"]
    list_filter = ["organization", "country", "is_active"]
    search_fields = ["name", "code"]


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ["name", "vendor_id", "organization", "category", "is_active"]
    list_filter = ["organization", "is_active"]
    search_fields = ["name", "vendor_id"]
