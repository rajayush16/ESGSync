from rest_framework.permissions import BasePermission

from apps.common.enums import UserRole


class IsOrganizationAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsDataManagerOrAbove(BasePermission):
    allowed_roles = {UserRole.ADMIN, UserRole.DATA_MANAGER}

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsAnalystOrAbove(BasePermission):
    allowed_roles = {UserRole.ADMIN, UserRole.DATA_MANAGER, UserRole.ANALYST}

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsAuditorOrAbove(BasePermission):
    allowed_roles = {UserRole.ADMIN, UserRole.AUDITOR}

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


class IsWithinOrganization(BasePermission):
    """Object-level permission: ensures the object belongs to the requesting user's org."""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        org = getattr(obj, "organization", None)
        if org is None:
            upload_session = getattr(obj, "upload_session", None)
            if upload_session:
                org = getattr(upload_session, "organization", None)
        return org == request.user.organization
