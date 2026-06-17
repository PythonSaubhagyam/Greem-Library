from django.urls import path
from .views import AuthView, RegisterView, LogoutView
from adminpanel.views import CustomerDashboardView , CoordinatorDashboardView


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
    path(
        "coordinator/dashboard/",
        CoordinatorDashboardView.as_view(),
        name="coordinator-dashboard",
    ),
]
