from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from rest_framework.permissions import IsAuthenticated
from adminpanel.pagination import ListPagination
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from adminpanel.Serializer.StudentDetailSerializer import *
from adminpanel.Serializer.StudentSerializer import *
from django.utils import timezone
from datetime import timedelta,datetime
from django.shortcuts import get_object_or_404
from django.db.models import Avg

class TeacherwiseStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        teacher_id = request.query_params.get('teacher_id')
        linked_user = request.GET.get("linked_user")
   

        student_id = request.GET.get('id')
        q = request.GET.get('q')
        students = StudentModel.objects.all().order_by('-id')
        
        if student_id:
            # print(student_id,'student_id')
            students = students.filter(id=student_id)

        
        if linked_user:
            students = students.filter(parent__id=linked_user)
        
            print(student_id)

 
        elif teacher_id:
            students = students.filter(parent__id=teacher_id)
 

        if q:
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
    

