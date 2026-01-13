from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from rest_framework.permissions import IsAuthenticated
from ..pagination import ListPagination
from django.utils import timezone
from datetime import timedelta





class StudentsAPIView(APIView):
    # permission_classes = [IsAuthenticated]
 
    def get(self, request):
        student_id = request.GET.get('id')
        q = request.GET.get('q')
        students = StudentModel.objects.all().order_by('-id')
        
        if student_id:
            # print(student_id,'student_id')
            students = students.filter(id=student_id)
        
        if q:
            print(q,'q')
            students = students.filter(
                Q(student_name__icontains=q) |
                Q(student_id__icontains=q) |
                Q(parent__last_name__icontains=q) |
                Q(parent__first_name__icontains=q) |
                Q(email__icontains=q) |
                Q(student_class__icontains=q)
            ).distinct()
        
        paginator = ListPagination()
        paginated_students = paginator.paginate_queryset(students,request)
        serializer = StudentsSerializer(paginated_students, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        serializer = StudentsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'data':serializer.data,'message':'Student successfully created'}, status=status.HTTP_201_CREATED)
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id):
        try:
            student = StudentModel.objects.get(id=id)
        except StudentModel.DoesNotExist:
            return Response({'errors':'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StudentsSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data':serializer.data,'message':'Student successfully updated'}, status=status.HTTP_200_OK)
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id):
        try:
            student = StudentModel.objects.get(id=id)
        except StudentModel.DoesNotExist:
            return Response({'errors':'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        student.delete()
        return Response({'message':'Student successfully deleted'}, status=status.HTTP_200_OK)
    