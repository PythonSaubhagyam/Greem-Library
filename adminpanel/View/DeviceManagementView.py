from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from web_project import TemplateHelper

from adminpanel.views import DashboardsView
from user_management.models import DeviceModel, StudentModel
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from user_management.models import DeviceModel
from adminpanel.Serializer.CustomerSerializer import DeviceMiniSerializer
from adminpanel.pagination import ListPagination
from django.db.models import Q

@method_decorator(login_required, name='dispatch')
class DeviceManagementView(DashboardsView):
    template_name = "device_management.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })

        user = request.user

        # Only devices belonging to students under this customer/principal
        students = StudentModel.objects.filter(parent=user)
        student_ids = list(students.values_list('id', flat=True))

        # Get devices linked to these students
        devices = DeviceModel.objects.filter(
            user=user  # devices assigned to this customer
        ).select_related('user').order_by('-id')

        # Stats
        total_devices = devices.count()
        active_devices = devices.filter(is_active=True).count()
        inactive_devices = devices.filter(is_active=False).count()

        context.update({
            'devices': devices,
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': inactive_devices,
            'total_students': students.count(),
        })

        return render(request, self.template_name, context)
    


class CustomerDeviceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        q = request.GET.get('q', '')

        # Only this customer's devices
        devices = DeviceModel.objects.filter(user=user).order_by('-id')

        if q:
            devices = devices.filter(
                Q(imei_number__icontains=q)
            )

        paginator = ListPagination()
        page = paginator.paginate_queryset(devices, request)
        serializer = DeviceMiniSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)