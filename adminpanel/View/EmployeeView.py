from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from user_management.models import EmployeeModel, UserModel
from adminpanel.Serializer.EmployeeSerializer import EmployeeDetailSerializer, EmployeeCreateSerializer
from ..pagination import ListPagination



class EmployeeAPIView(APIView):

    # 🔹 GET
    def get(self, request, pk=None):

        if pk:
            employee = get_object_or_404(EmployeeModel, pk=pk)
            serializer = EmployeeDetailSerializer(employee)
            return Response(serializer.data)

        paginator = ListPagination()
        employees = EmployeeModel.objects.select_related("user").order_by('-id')
        # optional role filter (e.g., ?role=Coordinator)
        role_param = request.GET.get('role')
        if role_param:
            employees = employees.filter(user__role__type__iexact=role_param)
        else:
            # If the requester is a Customer (school), show only employees for their firm
            try:
                req_user = request.user
                req_role = getattr(req_user.role, 'type', None) if getattr(req_user, 'role', None) else None
                if req_role and str(req_role).lower() == 'customer':
                    firm = getattr(req_user, 'firm_name', None)
                    # If firm present, restrict to employees whose user belongs to same firm or are linked to this customer
                    if firm:
                        related_users_qs = UserModel.objects.filter(firm_name__iexact=firm)
                        related_ids = list(related_users_qs.values_list('id', flat=True))
                        if related_ids:
                            employees = employees.filter(user__id__in=related_ids)
                    related_users_qs = UserModel.objects.filter(id=req_user.id)
                    if firm:
                        related_users_qs = related_users_qs | UserModel.objects.filter(firm_name__iexact=firm)
                    related_ids = list(related_users_qs.values_list('id', flat=True))
                    if related_ids:
                        employees = employees.filter(user__id__in=related_ids)
            except Exception:
                pass
        q= request.GET.get('q', '').strip()
        if q:
            employees = employees.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(department__icontains=q)
            )
        paginated_employees = paginator.paginate_queryset(employees, request)
        serializer = EmployeeDetailSerializer(paginated_employees, many=True)
        return paginator.get_paginated_response(serializer.data)

    # 🔹 POST → create User + Employee
    def post(self, request):

        serializer = EmployeeCreateSerializer(data=request.data)

        if serializer.is_valid():
            employee = serializer.save()
            return Response({'data': EmployeeDetailSerializer(employee).data,"employee_id": employee.id,'message':'Employee successfully created'},status=status.HTTP_201_CREATED)

        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # 🔹 PATCH → update both
    def patch(self, request, pk):

        employee = get_object_or_404(EmployeeModel, pk=pk)

        serializer = EmployeeCreateSerializer(
            employee,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            employee = serializer.save()
            return Response({'data': EmployeeDetailSerializer(employee).data,"employee_id": employee.id, 'message': 'Employee successfully updated'}, status=status.HTTP_200_OK)

        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # 🔹 DELETE → delete employee + user
    def delete(self, request, pk):

        employee = get_object_or_404(EmployeeModel, pk=pk)

        user = employee.user
        employee.delete()
        user.delete()

        return Response(
            {"message": "Employee and user deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
