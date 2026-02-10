from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from user_management.models import EmployeeModel
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
