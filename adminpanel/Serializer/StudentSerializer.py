from rest_framework import serializers
from django.utils import timezone

from tablet_app.models import StudentTestAttemptModel
from user_management.models import *


class StudentsSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    device_imei_number = serializers.CharField(source='device_id.imei_number', read_only=True)
    imei_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def get_parent_name(self, obj):
        parents = []
        if obj.parent.exists():
            for parent in obj.parent.all():
                if parent.role.type == 'Parent':
                    parents.append(f"{parent.first_name} {parent.last_name}")
            return parents

        return ''
    
    def get_teacher_name(self, obj):
        teachers = []
        if obj.parent.exists():
            for parent in obj.parent.all():
                if parent.role.type == 'Teacher':
                    teachers.append(f"{parent.first_name} {parent.last_name}")
            return teachers
                
        return ''

    def get_customer_name(self, obj):
        if obj.parent.exists():
            for parent in obj.parent.all():
                if parent.role.type == 'Customer':
                    return f"{parent.first_name} {parent.last_name}"
        return ''
    
    def create(self, validated_data):
        request = self.context.get("request")
        imei_number = validated_data.pop("imei_number", None)
        if StudentModel.objects.filter(device_id__imei_number=imei_number).exists():
            raise serializers.ValidationError({"error": "This IMEI is already assigned to another student."})
        try:
            device = DeviceModel.objects.get(imei_number=imei_number)
        except DeviceModel.DoesNotExist:
            raise serializers.ValidationError({"error": "Device with this IMEI does not exist."})
        validated_data["device_id"] = device
        student = super().create(validated_data)
        # if parent_ids:
        #     parents = UserModel.objects.filter(id__in=parent_ids)
        #     student.parent.set(parents)
        return student
    
    def update(self, instance, validated_data):
        parents = validated_data.get("parent", None)
        imei_number = validated_data.pop("imei_number", None)
        if imei_number:
            if StudentModel.objects.filter(device_id__imei_number=imei_number).exists():
              raise serializers.ValidationError({"error": "This IMEI is already assigned to another student."})
            try:
                device = DeviceModel.objects.get(imei_number=imei_number)
                instance.device_id = device
            except DeviceModel.DoesNotExist:
                raise serializers.ValidationError("Device with this IMEI does not exist.")
        print(parents,'parentsparentsparents')
        instance = super().update(instance, validated_data)
        # if parents is not None:
        #     instance.parent.set(parents)
        return instance 

    class Meta:
        model = StudentModel
        fields = ['id', 'imei_number','device_imei_number','student_name','parent_name','teacher_name','email','parent','customer_name','student_class']



