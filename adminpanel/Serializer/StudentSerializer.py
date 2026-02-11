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
        print(validated_data,'validated_datavalidated_datavalidated_data')
        request = self.context.get("request")
        imei_number = validated_data.pop("imei_number", None)
        if StudentModel.objects.filter(device_id__imei_number=imei_number).exists():
            raise serializers.ValidationError({"error": "This IMEI is already assigned to another student."})
        try:
            device = DeviceModel.objects.get(imei_number=imei_number)
        except DeviceModel.DoesNotExist:
            raise serializers.ValidationError({"error": "Device with this IMEI does not exist."})
        if device.user not in  validated_data.get("parent", None):
            name = f"{device.user.first_name} {device.user.last_name}"
            raise serializers.ValidationError({"error": f"This Device is already assigned to the {name}."})
        validated_data["device_id"] = device
        student = super().create(validated_data)
        # if parent_ids:
        #     parents = UserModel.objects.filter(id__in=parent_ids)
        #     student.parent.set(parents)
        return student
    
    def update(self, instance, validated_data):
        parents = validated_data.pop("parent", None)
        imei_number = validated_data.pop("imei_number", None)
        if imei_number:
           
            if instance.device_id and instance.device_id.imei_number == imei_number:
               pass
            else:
                if not StudentModel.objects.filter(device_id__imei_number=imei_number).exclude(id=instance.id).exists():
                   raise serializers.ValidationError({"error": "This IMEI is already assigned to another student."})
                try:
                    device = DeviceModel.objects.get(imei_number=imei_number) 
                    print(validated_data.get("parent", None)[0])
                    if device.user not in  validated_data.get("parent", None):
                        name = f"{device.user.first_name} {device.user.last_name}"
                        raise serializers.ValidationError({"error": f"This Device is already assigned to the {name}."})
                    instance.device_id = device
                except DeviceModel.DoesNotExist:
                    raise serializers.ValidationError("Device with this IMEI does not exist.")
        print(parents,'parentsparentsparents')
        instance = super().update(instance, validated_data)
        if parents is not None:

            existing = instance.parent.all()

            # keep parents + teachers always
            protected = existing.exclude(role__type="Customer")

            # remove old customer(s), add new one(s)
            final = list(protected) + list(parents)

            instance.parent.set(final)
        return instance 

    class Meta:
        model = StudentModel
        fields = ['id', 'imei_number','device_imei_number','student_name','parent_name','teacher_name','email','parent','customer_name','student_class']



