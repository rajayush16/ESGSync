from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.enums import UserRole
from .models import Facility, Organization, User, Vendor


class OrganizationSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id", "name", "slug", "industry_sector", "country",
            "reporting_year_start", "fiscal_year_end_month",
            "is_active", "max_users", "user_count", "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "user_count"]

    def get_user_count(self, obj) -> int:
        return obj.users.filter(is_active=True).count()


class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "organization", "organization_name", "role",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email", "first_name", "last_name", "password",
            "confirm_password", "role",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        organization = self.context["request"].user.organization
        user = User.objects.create_user(
            organization=organization,
            **validated_data,
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "role", "is_active"]


class ESGSyncTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["org_id"] = str(user.organization_id) if user.organization_id else None
        token["org_slug"] = user.organization.slug if user.organization else None
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.get_full_name(),
            "role": self.user.role,
            "organization_id": str(self.user.organization_id) if self.user.organization_id else None,
            "organization_name": self.user.organization.name if self.user.organization else None,
        }
        return data


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = [
            "id", "name", "code", "address", "city", "country",
            "region", "latitude", "longitude", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id", "name", "vendor_id", "category", "country",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
