import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.enums import UserRole
from apps.common.models import BaseModel, SoftDeleteModel


class Organization(SoftDeleteModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    industry_sector = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    reporting_year_start = models.IntegerField(default=1)  # month number
    fiscal_year_end_month = models.IntegerField(default=12)
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=50)
    settings = models.JSONField(default=dict)

    class Meta:
        db_table = "organizations"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.ANALYST,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["organization", "role"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.email

    def can_approve_records(self) -> bool:
        return self.role in {UserRole.ADMIN, UserRole.DATA_MANAGER, UserRole.ANALYST}

    def can_manage_uploads(self) -> bool:
        return self.role in {UserRole.ADMIN, UserRole.DATA_MANAGER}

    def is_auditor(self) -> bool:
        return self.role in {UserRole.ADMIN, UserRole.AUDITOR}


class Facility(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="facilities",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "facilities"
        unique_together = [("organization", "code")]
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Vendor(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="vendors",
    )
    name = models.CharField(max_length=255)
    vendor_id = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vendors"
        unique_together = [("organization", "vendor_id")]
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.vendor_id})"
