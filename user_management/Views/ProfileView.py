from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import *
from user_management.Serializers.UserSerializer import *
from django.conf import settings
import random
from django.utils import timezone


class ProfileView(APIView):
    
    def get(self,request):
        user = UserModel.objects.filter(id=request.user.id).first()
        if user is not None:
            serializer = ProfileSerializer(user)
            return Response({'status':True,'data':serializer.data,'message':'Profile Successfully retreived'})
        return Response({'status':False,'message':'Profile not Available'},status=400)
    
    def patch(self,request,id):
        try:
            user = UserModel.objects.get(id=id)
            serializer = ProfileSerializer(user,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':True,'message':'Profile Successfully updated'},status=200)
            return Response({'status':False,'errors':serializer.errors})
        except UserModel.DoesNotExist:
            return Response({'status':False,'message':'User not available'},status=400)