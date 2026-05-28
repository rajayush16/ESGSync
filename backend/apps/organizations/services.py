from typing import Optional

import structlog

from apps.common.exceptions import OrganizationException
from apps.common.utils import slugify_org_name
from .models import Facility, Organization, User, Vendor

logger = structlog.get_logger(__name__)


class OrganizationService:
    @staticmethod
    def create_organization(name: str, **kwargs) -> Organization:
        slug = slugify_org_name(name)
        base_slug = slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization.objects.create(name=name, slug=slug, **kwargs)
        logger.info("organization_created", org_id=str(org.id), name=name, slug=slug)
        return org

    @staticmethod
    def get_organization_by_slug(slug: str) -> Organization:
        try:
            return Organization.objects.get(slug=slug, is_active=True)
        except Organization.DoesNotExist:
            raise OrganizationException(f"Organization '{slug}' not found.")

    @staticmethod
    def deactivate_organization(org: Organization, performed_by: User) -> None:
        if not performed_by.is_staff:
            raise OrganizationException("Only platform administrators can deactivate organizations.")
        org.is_active = False
        org.save(update_fields=["is_active", "updated_at"])
        logger.warning("organization_deactivated", org_id=str(org.id), by=str(performed_by.id))


class UserService:
    @staticmethod
    def get_users_for_org(organization: Organization):
        return (
            User.objects.filter(organization=organization, is_active=True)
            .select_related("organization")
            .order_by("last_name", "first_name")
        )

    @staticmethod
    def invite_user(
        organization: Organization,
        email: str,
        first_name: str,
        last_name: str,
        role: str,
        temp_password: str,
    ) -> User:
        if User.objects.filter(email=email).exists():
            raise OrganizationException(f"A user with email '{email}' already exists.")

        active_user_count = User.objects.filter(
            organization=organization, is_active=True
        ).count()
        if active_user_count >= organization.max_users:
            raise OrganizationException(
                f"Organization has reached its user limit of {organization.max_users}."
            )

        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization=organization,
            role=role,
            password=temp_password,
        )
        logger.info("user_invited", user_id=str(user.id), org_id=str(organization.id), role=role)
        return user

    @staticmethod
    def deactivate_user(user: User, performed_by: User) -> None:
        if user.id == performed_by.id:
            raise OrganizationException("You cannot deactivate your own account.")
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        logger.info("user_deactivated", user_id=str(user.id), by=str(performed_by.id))


class FacilityService:
    @staticmethod
    def get_or_create_facility(
        organization: Organization,
        code: str,
        name: str,
        **kwargs,
    ) -> tuple[Facility, bool]:
        return Facility.objects.get_or_create(
            organization=organization,
            code=code,
            defaults={"name": name, **kwargs},
        )


class VendorService:
    @staticmethod
    def get_or_create_vendor(
        organization: Organization,
        vendor_id: str,
        name: str,
        **kwargs,
    ) -> tuple[Vendor, bool]:
        if vendor_id:
            return Vendor.objects.get_or_create(
                organization=organization,
                vendor_id=vendor_id,
                defaults={"name": name, **kwargs},
            )
        vendor = Vendor.objects.create(
            organization=organization,
            vendor_id="",
            name=name,
            **kwargs,
        )
        return vendor, True
