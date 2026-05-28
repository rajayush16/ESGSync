from rest_framework.routers import DefaultRouter
from .views import EmissionRecordViewSet

router = DefaultRouter()
router.register("", EmissionRecordViewSet, basename="emission-record")

urlpatterns = router.urls
