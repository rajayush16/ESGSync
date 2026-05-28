from rest_framework.routers import DefaultRouter
from .views import DataSourceViewSet, SuspiciousRecordViewSet, UploadSessionViewSet

router = DefaultRouter()
router.register("sources", DataSourceViewSet, basename="data-source")
router.register("sessions", UploadSessionViewSet, basename="upload-session")
router.register("suspicious", SuspiciousRecordViewSet, basename="suspicious-record")

urlpatterns = router.urls
