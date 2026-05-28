from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.organizations.views import (
    OrganizationViewSet,
    UserViewSet,
    FacilityViewSet,
    VendorViewSet,
)

router = DefaultRouter()
router.register("", OrganizationViewSet, basename="organization")
router.register(r"(?P<org_slug>[^/.]+)/users", UserViewSet, basename="organization-user")
router.register(r"(?P<org_slug>[^/.]+)/facilities", FacilityViewSet, basename="facility")
router.register(r"(?P<org_slug>[^/.]+)/vendors", VendorViewSet, basename="vendor")

urlpatterns = router.urls
