from rest_framework import serializers
from ..models import *

class SignUpSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','email','mobile_no']
        
        
class ProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.type',default='')
    
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','email','mobile_no','role','address']