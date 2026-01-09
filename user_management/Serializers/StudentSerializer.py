from rest_framework import serializers
from ..models import *


class StudentSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['parent'] = request.user
        
        student_id = validated_data.get('student_id')
        if StudentModel.objects.filter(student_id=student_id).exists():
            raise serializers.ValidationError({'error':'Student already exists'})
        
        return super().create(validated_data)  
    
    class Meta:
        model = StudentModel
        fields = ['id','student_id','parent','student_name','email','student_class']