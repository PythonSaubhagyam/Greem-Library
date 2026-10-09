from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import *
from user_management.Serializers.UserSerializer import *
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import random
from django.utils import timezone

class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self,request):
        
        email = request.data.get('email')
        mobile_no = request.data.get('mobile_no')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        password = request.data.get('password', '')
        role = request.data.get('role', '')  

        role_obj = None
        if role:
            role_obj = RoleModel.objects.filter(id=role).first()

        data = request.data.copy()
        data['role'] = role_obj.id if role_obj else None
        serializer = SignUpSerializer(data=data)
                
        # if not email or not mobile_no or not first_name or not last_name or not password:
        #     return Response({'status': False, 'message': 'Email, Mobile no, First name, Last name and Password are required'}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'status': False, 'message': 'Email is required'},status=status.HTTP_400_BAD_REQUEST)
        if not mobile_no :
            return Response({'status': False, 'message': 'Mobile no is required'},status=status.HTTP_400_BAD_REQUEST)
        if not first_name or not last_name:
            return Response({'status': False, 'message': 'First name and Last name are required'},status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'status': False, 'message': 'Password is required'},status=status.HTTP_400_BAD_REQUEST)

        try:
            if UserModel.objects.filter(email=email).exists():
                return Response({'status': False, 'message': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = SignUpSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'data':serializer.data,'message':'You have successfully registered'})
            return Response({'status':False,'errors':serializer.errors})
        
        except Exception as e:
            return Response({'error': "Something went wrong", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)