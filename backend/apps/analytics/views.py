from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAnalystOrAbove
from .services import DashboardAnalyticsService


class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        data = DashboardAnalyticsService.get_overview(request.user.organization)
        return Response(data)


class EmissionsByMonthView(APIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        year = request.query_params.get("year")
        scope = request.query_params.get("scope")
        data = DashboardAnalyticsService.get_emissions_by_month(
            request.user.organization,
            year=int(year) if year else None,
            scope=scope or None,
        )
        return Response(data)


class UploadStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        data = DashboardAnalyticsService.get_upload_stats(request.user.organization)
        return Response(data)


class SuspiciousSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]

    def get(self, request):
        data = DashboardAnalyticsService.get_suspicious_summary(request.user.organization)
        return Response(data)
