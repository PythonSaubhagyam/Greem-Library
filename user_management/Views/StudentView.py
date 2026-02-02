from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import *
from user_management.Serializers.StudentSerializer import *
from django.conf import settings
import random
from django.utils import timezone



class StudentView(APIView):
    
    def get(self,request):
        students = StudentModel.objects.filter(parent_id=request.user.id)
        serializer = StudentSerializer(students,many=True)
        return Response({'status':True,'data':serializer.data,'message':'Student successfully retrieved'})
        
    
    def post(self,request):
        data = request.data
        serializer = StudentSerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response({'status':True,'data':serializer.data,'message':'Student Successfully added'})
        return Response({'status':False,'errors':serializer.errors},status=400)
    
    def patch(self,request,id):
        try:
            student =  StudentModel.objects.get(id=id)
            serializer = StudentSerializer(student,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'message':'Student updated successfully'})
            
            return Response({'status':False,'errors':serializer.errors},status=500)

        except StudentModel.DoesNotExist:
             return Response({'status':False,'message':'Student not available'},status=400)
    
    def delete(self,request,id):
        try:
            student =  StudentModel.objects.get(id=id)
            student.delete()
            return Response({'status':True,'message':'Student Removed successfully'})
        except StudentModel.DoesNotExist:
             return Response({'status':False,'message':'Student not available'},status=400)
        