from rest_framework import serializers
from user_management.models import *


class AddStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentModel
        fields = ['id', 'student_name', 'email', 'student_class', 'device_id', 'parent']
        extra_kwargs = {
            'student_class': {'required': True},
            'device_id': {'required': False},
            'parent': {'required': False},
        }

    # def validate_student_class(self, value):
    #     teacher = self.context['request'].user

    #     # Teacher is allowed if they own the class OR are assigned to it via TeacherAssignmentModel
    #     is_class_owner = value.teacher_id == teacher.id
    #     is_assigned = TeacherAssignmentModel.objects.filter(
    #         teacher=teacher, assigned_classes=value, is_active=True
    #     ).exists()

    #     if not (is_class_owner or is_assigned):
    #         raise serializers.ValidationError("You are not assigned to this class")
    #     return value


class StudentListSerializer(serializers.ModelSerializer):
    class_id = serializers.IntegerField(source='student_class.id', default=None)
    class_name = serializers.CharField(source='student_class.classname', default='')
    standard = serializers.IntegerField(source='student_class.standard', default=None)
    section = serializers.CharField(source='student_class.section', default='')

    class Meta:
        model = StudentModel
        fields = ['id', 'student_name', 'class_id','email', 'class_name', 'standard', 'section']