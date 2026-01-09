from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate,login
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import *
from user_management.Serializers.UserSerializer import *
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import random
from django.utils import timezone


class SignInView(APIView):
    
    def post(self,request):
        
        try:
            email = request.data.get('email','')
            password = request.data.get('password','')
            
            if UserModel.objects.get(email=email).is_active == True:
            
                auth_user = authenticate(username=email, password=password)
                
                if auth_user is not None and auth_user.role:
                    data = dict()
                    obj, _ = Token.objects.get_or_create(user=auth_user)
                    login(request, auth_user)
                    data['id'] = auth_user.id
                    data['first_name'] = auth_user.first_name
                    data['last_name'] = auth_user.last_name
                    data['email'] = auth_user.email
                    data['token'] = obj.key
                    
                    return Response({'status': True, 'data': data, 'message': 'User successfully logged In'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
        
            else:
                    return Response({'status': False, 'message': 'Your account has been deactivated!'}, status=status.HTTP_400_BAD_REQUEST)
        except UserModel.DoesNotExist:
            return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
                