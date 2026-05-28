from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

from apps.organizations.views import (
    ESGSyncTokenObtainPairView,
    CurrentUserView,
    ChangePasswordView,
)

urlpatterns = [
    path("token/", ESGSyncTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]
