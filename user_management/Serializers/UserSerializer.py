from rest_framework import serializers
from ..models import *
from django.contrib.auth.hashers import make_password


class SignUpSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','email','mobile_no','password', 'role']
        
    def create(self, validated_data):
        role = validated_data.pop('role', None)
        validated_data['password'] = make_password(validated_data['password'])

        user = super().create(validated_data)

        if role:
            user.role = role
            user.save()

        return user  
    
class ProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.type',default='')
    
    class Meta:
        model = UserModel
        fields = ['id','first_name','last_name','email','mobile_no','role','address']