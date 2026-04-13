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

            user = UserModel.objects.filter(email=email).first()
            if not user:
                return Response(
                    {'status': False, 'message': 'Invalid credentials!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user.is_active:
                print("active")
                auth_user = authenticate(username=email, password=password)
                    
                if auth_user is not None:
                    data = dict()
                    obj, _ = Token.objects.get_or_create(user=auth_user)
                    login(request, auth_user)
                    data['id'] = auth_user.id
                    data['first_name'] = auth_user.first_name
                    data['last_name'] = auth_user.last_name
                    data['email'] = auth_user.email
                    data['role'] = auth_user.role.type if auth_user.role else ''
                    data['token'] = obj.key
                    
                    return Response({'status': True, 'data': data, 'message': 'User successfully logged In'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)
        
            else:
                    return Response({'status': False, 'message': 'Your account has been deactivated!'}, status=status.HTTP_400_BAD_REQUEST)
        except UserModel.DoesNotExist:
            return Response({'status': False, 'message': 'Invalid credentials!'}, status=status.HTTP_400_BAD_REQUEST)


class QRLoginAPIView(APIView):

    def post(self, request):
        imei_number = request.data.get('imei_number')

        if not imei_number:
            return Response({
                "status": False,
                "message": "IMEI / Device ID required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find Device
            device = DeviceModel.objects.get(
                imei_number=imei_number,
                is_active=True
            )

            # Find Student (for parent login)
            student = StudentModel.objects.filter(device_id=device).first()

            user = None
            login_type = None

            #  Parent Login Flow
            if student and student.parent.exists():
                user = student.parent.first()
                login_type = "Parent"

            #  Teacher Login Flow (example: device linked directly to teacher)
            elif device.user and device.user.role and device.user.role.type == "Teacher":
                user = device.user
                login_type = "Teacher"

            if not user:
                return Response({
                    "status": False,
                    "message": "No user linked with this device"
                }, status=status.HTTP_404_NOT_FOUND)

            #  Check Active
            if not user.is_active:
                return Response({
                    "status": False,
                    "message": "User is deactivated"
                }, status=status.HTTP_403_FORBIDDEN)

            # Login
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)

            data = {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role.type if user.role else '',
                "token": token.key,
                "login_type": login_type
            }

            # Extra info for parent
            if login_type == "Parent":
                data["student_name"] = student.student_name

            return Response({
                "status": True,
                "message": f"{login_type} login successful",
                "data": data
            }, status=status.HTTP_200_OK)

        except DeviceModel.DoesNotExist:
            return Response({
                "status": False,
                "message": "Invalid QR / Device not found"
            }, status=status.HTTP_400_BAD_REQUEST)