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


class ProfileUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='profile_image', required=False, allow_null=True)

    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'email', 'mobile_no', 'image']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'mobile_no': {'required': False},
        }

    def validate_email(self, value):
        user = self.instance
        if UserModel.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already exists")
        return value