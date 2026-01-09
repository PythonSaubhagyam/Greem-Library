from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
# from account.models import FacebookMetadata


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to dashboards/urls.py file for more pages.
"""


class DashboardsView(LoginRequiredMixin, TemplateView):

    template_name = "dashboard_analytics.html"
    def get_template_names(self):
        user = self.request.user
        # if user.role.name == "Admin" and user.id in settings.ADMIN_IDS:
        #     return ["dashboard_panel.html"]  # new admin dashboard
        return [self.template_name]

    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        # context['ADMIN_IDS'] = settings.ADMIN_IDS
        # context['admin_company_id']  = FacebookMetadata.objects.filter(user__email="info@saubhagyam.com").first().id if FacebookMetadata.objects.filter(user__email="info@saubhagyam.com").exists() else "ID Not Found"
        context['request'] = self.request

        return context


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password1 = request.data.get("new_password1")
        new_password2 = request.data.get("new_password2")

        if not user.check_password(current_password):
            return Response(
                {"success": False, "error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password1 != new_password2:
            return Response(
                {"success": False, "error": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password1) < 6:
            return Response(
                {"success": False, "error": "Password must be at least 6 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password1)
        user.save()

        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)  # Prevent logout after password change

        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )