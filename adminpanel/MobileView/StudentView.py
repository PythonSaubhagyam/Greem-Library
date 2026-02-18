from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from ..pagination import ListPagination
from adminpanel.Serializer.StudentDetailSerializer import *
from adminpanel.Serializer.StudentSerializer import *


class MobileStudentsAPIView(APIView):
 
    def get(self, request):
        imei_number = request.GET.get('imei_number')
        q = request.GET.get('q')
        students = StudentModel.objects.all().order_by('-id')
        

        if imei_number:
            # print(imei_number,'imei_number')
            students = students.filter(device_id__imei_number=imei_number)
        
        if q:
            print(q,'q')
            students = students.filter(
                Q(student_name__icontains=q) |
                Q(device_id__imei_number__icontains=q) |
                Q(parent__last_name__icontains=q) |
                Q(parent__first_name__icontains=q) |
                Q(email__icontains=q) |
                Q(student_class__icontains=q)
            ).distinct()
        
        paginator = ListPagination()
        paginated_students = paginator.paginate_queryset(students,request)
        serializer = StudentsSerializer(paginated_students, many=True)
        return paginator.get_paginated_response(serializer.data)

    
    def patch(self, request):
        imei_number = request.query_params.get('imei_number')
        if not imei_number:
            return Response({'errors': 'IMEI number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = StudentModel.objects.get(device_id__imei_number=imei_number)
        except StudentModel.DoesNotExist:
            return Response({'errors': f'Student with IMEI {imei_number} not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        new_imei = data.get('imei_number')
        if new_imei:
            try:
                device = DeviceModel.objects.get(imei_number=new_imei)
                data['device_id'] = device.id
            except DeviceModel.DoesNotExist:
                return Response({'errors': f"Device with IMEI {new_imei} does not exist."},
                                status=status.HTTP_400_BAD_REQUEST)

        customer_id = data.get('customer')
        if customer_id:
            data['parent'] = [customer_id]

        serializer = StudentsSerializer(student, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            if customer_id:
                student.parent.set(UserModel.objects.filter(id=customer_id))
            return Response({'data': serializer.data, 'message': 'Student successfully updated'}, status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    

    def delete(self,request,id):
        try:
            student = StudentModel.objects.get(device_id__imei_number=id)
        except StudentModel.DoesNotExist:
            return Response({'errors':'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        student.delete()
        return Response({'message':'Student successfully deleted'}, status=status.HTTP_200_OK)

