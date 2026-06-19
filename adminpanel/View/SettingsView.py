from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from web_project import TemplateHelper

from adminpanel.views import DashboardsView
from user_management.models import UserModel


@method_decorator(login_required, name='dispatch')
class SettingsView(DashboardsView):
    template_name = "settings.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "user": request.user,
        })
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        action = request.POST.get('action')

        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.mobile_no = request.POST.get('mobile_no', user.mobile_no)
            user.firm_name = request.POST.get('firm_name', user.firm_name)
            user.save()
            return JsonResponse({'status': True, 'message': 'Profile updated successfully'})

        if action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not user.check_password(old_password):
                return JsonResponse({'status': False, 'message': 'Old password is incorrect'})
            if new_password != confirm_password:
                return JsonResponse({'status': False, 'message': 'Passwords do not match'})
            if len(new_password) < 6:
                return JsonResponse({'status': False, 'message': 'Password must be at least 6 characters'})

            user.set_password(new_password)
            user.save()
            return JsonResponse({'status': True, 'message': 'Password changed successfully. Please login again.'})

        return JsonResponse({'status': False, 'message': 'Invalid action'})