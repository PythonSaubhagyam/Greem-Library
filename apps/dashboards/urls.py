from django.urls import path
from .views import DashboardsView,ChangePasswordAPIView
from .DashboardView import DashboardStatsAPIView

urlpatterns = [
    path(
        "",
        DashboardsView.as_view(template_name="dashboard_analytics.html"),
        name="index",
    ),
    path(
        "admin-dashboard/",
        DashboardsView.as_view(template_name="dashboard_panel.html"),
        name="admin-dashboard",
    ),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path('admin_api/dashboard-stats/', DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    # path("admin_api/company-stats/", CompanyStatsAPIView.as_view(), name="company-stats"),
]
