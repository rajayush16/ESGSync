from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

import structlog

from apps.audit.services import AuditService
from apps.common.enums import AuditAction, UserRole
from apps.common.permissions import IsAnalystOrAbove, IsDataManagerOrAbove, IsOrganizationAdmin
from .models import Facility, Organization, User, Vendor
from .serializers import (
    ESGSyncTokenObtainPairSerializer,
    FacilitySerializer,
    OrganizationSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    VendorSerializer,
)
from .services import FacilityService, OrganizationService, UserService, VendorService

logger = structlog.get_logger(__name__)


class ESGSyncTokenObtainPairView(TokenObtainPairView):
    serializer_class = ESGSyncTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data.get("email"))
            ip = request.META.get("REMOTE_ADDR")
            user.last_login_ip = ip
            user.save(update_fields=["last_login_ip"])
            AuditService.log(
                action=AuditAction.USER_LOGIN,
                performed_by=user,
                organization=user.organization,
                description=f"User {user.email} logged in.",
                ip_address=ip,
            )
        return response


class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not user.check_password(current_password):
            return Response(
                {"error": {"code": "invalid_password", "message": "Current password is incorrect."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password or "") < 8:
            return Response(
                {"error": {"code": "weak_password", "message": "New password must be at least 8 characters."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password updated successfully."})


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user.is_staff:
            return Organization.objects.all()
        if self.request.user.organization:
            return Organization.objects.filter(id=self.request.user.organization_id)
        return Organization.objects.none()

    def perform_create(self, serializer):
        org = OrganizationService.create_organization(
            name=serializer.validated_data["name"],
            **{k: v for k, v in serializer.validated_data.items() if k != "name"},
        )
        serializer.instance = org


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDataManagerOrAbove]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        return UserService.get_users_for_org(self.request.user.organization)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        UserService.deactivate_user(user, performed_by=request.user)
        return Response({"message": f"User {user.email} deactivated."})


class FacilityViewSet(viewsets.ModelViewSet):
    serializer_class = FacilitySerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return Facility.objects.filter(
            organization=self.request.user.organization,
            is_active=True,
        )

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return Vendor.objects.filter(
            organization=self.request.user.organization,
            is_active=True,
        )

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
