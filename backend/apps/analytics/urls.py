from django.urls import path
from .views import (
    DashboardOverviewView,
    EmissionsByMonthView,
    SuspiciousSummaryView,
    UploadStatsView,
)

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="analytics-overview"),
    path("emissions-by-month/", EmissionsByMonthView.as_view(), name="emissions-by-month"),
    path("upload-stats/", UploadStatsView.as_view(), name="upload-stats"),
    path("suspicious-summary/", SuspiciousSummaryView.as_view(), name="suspicious-summary"),
]
