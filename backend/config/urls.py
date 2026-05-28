from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/auth/", include("apps.organizations.urls.auth")),
    path("api/v1/organizations/", include("apps.organizations.urls.organizations")),
    path("api/v1/uploads/", include("apps.ingestion.urls")),
    path("api/v1/emissions/", include("apps.emissions.urls")),
    path("api/v1/reviews/", include("apps.reviews.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
