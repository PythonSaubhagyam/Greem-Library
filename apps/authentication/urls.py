from django.urls import path
from .views import AuthView, RegisterView, LogoutView
from adminpanel.views import CustomerDashboardView , CoordinatorDashboardView
from adminpanel.View.TestsView import TestDetailView
from adminpanel.View.StudyTimeView import StudyTimeView
from adminpanel.View.WeaknessAnalysisView import WeaknessAnalysisView
from adminpanel.View.ReportsView import ReportsView
from adminpanel.View.AlertsView import AlertsView
from adminpanel.View.DeviceManagementView import *
from adminpanel.View.SettingsView import SettingsView
from adminpanel.View.CoordinatorsView import CoordinatorsView

urlpatterns = [
    path(
        "auth/login/",
        AuthView.as_view(template_name="auth_login_basic.html"),
        name="auth-login-basic",
    ),
    path(
        "accounts/login/",
        AuthView.as_view(template_name="auth_login_basic.html"),
        name="auth-login-basic",
    ),
    path(
        "auth/register/",
        RegisterView.as_view(),
        name="auth-register-basic",
    ),
    path(
        "auth/forgot_password/",
        AuthView.as_view(template_name="auth_forgot_password_basic.html"),
        name="auth-forgot-password-basic",
    ),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path(
        "customer/dashboard/",
        CustomerDashboardView.as_view(),
        name="customer-dashboard",
    ),
    # 15 Modules from Specification
    path("customer/dashboard/school-setup/", CustomerDashboardView.as_view(template_name="add_company.html"), name="customer-school-setup"),
    path("customer/dashboard/students/", CustomerDashboardView.as_view(template_name="Students_list.html"), name="customer-students"),
    path("customer/dashboard/classes/", CustomerDashboardView.as_view(template_name="Classes_list.html"), name="customer-classes"),
    path("customer/dashboard/classes/add/", CustomerDashboardView.as_view(template_name="classes_add_update.html"), name="customer-classes-add"),
    path("customer/dashboard/classes/edit/<int:id>/", CustomerDashboardView.as_view(template_name="classes_add_update.html"), name="customer-classes-edit"),
    path("customer/dashboard/teachers/", CustomerDashboardView.as_view(template_name="companies_list.html"), name="customer-teachers"),
    path("customer/dashboard/subjects/", CustomerDashboardView.as_view(template_name="company_detail.html"), name="customer-subjects"),
    path("customer/dashboard/tests/", CustomerDashboardView.as_view(template_name="tests_list.html"), name="customer-tests"),
    path("customer/dashboard/tests/add/", CustomerDashboardView.as_view(template_name="tests_add.html"), name="customer-tests-add"),
    path("customer/dashboard/tests/<int:pk>/", TestDetailView.as_view(), name="customer-test-detail"),
    path("customer/dashboard/homework/", CustomerDashboardView.as_view(template_name="homework_reports.html"), name="customer-homework"),
    path("customer/dashboard/homework/add/", CustomerDashboardView.as_view(template_name="homework_add.html"), name="customer-homework-add"),
    path("customer/dashboard/study-time/", StudyTimeView.as_view(), name="customer-study-time"),
    path("customer/dashboard/weakness-analysis/", WeaknessAnalysisView.as_view(), name="customer-weakness"),
    path("customer/dashboard/reports/", ReportsView.as_view(), name="customer-reports"),
    path("customer/dashboard/alerts/", AlertsView.as_view(), name="customer-alerts"),
    path("customer/dashboard/device-management/", DeviceManagementView.as_view(), name="customer-device-mgmt"),
    path("customer/dashboard/devices-api/", CustomerDeviceAPIView.as_view(), name="customer-devices-api"),
    path("customer/dashboard/settings/", SettingsView.as_view(), name="customer-settings"),
    path("customer/dashboard/coordinators/", CoordinatorsView.as_view(), name="customer-coordinators"),

    # Added alternate URL to match incoming link/typo `customers-dashbord/`
    path(
        "customers-dashbord/",
        CustomerDashboardView.as_view(),
        name="customers-dashbord",
    ),
    path(
        "coordinator/dashboard/",
        CoordinatorDashboardView.as_view(),
        name="coordinator-dashboard",
    ),
]
