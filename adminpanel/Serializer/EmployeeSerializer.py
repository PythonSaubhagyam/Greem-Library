from rest_framework import serializers
from user_management.models import *
from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField


class EmployeeCreateSerializer(serializers.ModelSerializer):

    # ---- USER FIELDS ----
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    mobile_no = serializers.CharField(max_length=15, required=False, allow_null=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = EmployeeModel
        fields = [
            # Employee fields
            "employee_id",
            "department",

            # User fields
            "email",
            "first_name",
            "last_name",
            "mobile_no",
            "password",
        ]
    
    def validate_email(self, value):

        qs = UserModel.objects.filter(email=value)

        # while updating exclude current user
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)

        if qs.exists():
            raise serializers.ValidationError(
                "This email is already existed."
            )

        return value

    # -----------------------------
    # ✅ EMPLOYEE ID VALIDATION
    # -----------------------------
    def validate_employee_id(self, value):

        qs = EmployeeModel.objects.filter(employee_id=value)

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "Employee ID already exists."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):

        # --- pop user data ---
        password = validated_data.pop("password")

        user_data = {
            "email": validated_data.pop("email"),
            "first_name": validated_data.pop("first_name"),
            "last_name": validated_data.pop("last_name"),
            "mobile_no": validated_data.pop("mobile_no", None),
        }

        # ---- Assign Employee Role ----
        role = RoleModel.objects.filter(type="Employee").first()
        user_data["role"] = role

        user = UserModel.objects.create(**user_data)
        user.set_password(password)
        user.save()

        # ---- Create Employee ----
        employee = EmployeeModel.objects.create(
            user=user,
            email=user.email,
            **validated_data
        )

        return employee
    
    @transaction.atomic
    def update(self, instance, validated_data):

        user = instance.user

        # ---- USER FIELDS ----
        if "email" in validated_data:
            user.email = validated_data.pop("email")

        if "first_name" in validated_data:
            user.first_name = validated_data.pop("first_name")

        if "last_name" in validated_data:
            user.last_name = validated_data.pop("last_name")

        if "mobile_no" in validated_data:
            user.mobile_no = validated_data.pop("mobile_no")

        if "password" in validated_data:
            user.set_password(validated_data.pop("password"))

        user.save()

        # ---- EMPLOYEE FIELDS ----
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.email = user.email  # keep in sync
        instance.save()

        return instance
    
class EmployeeDetailSerializer(serializers.ModelSerializer):

    user = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeModel
        fields = [
            "id",
            "employee_id",
            "department",
            "email",
            "user",
        ]

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "mobile_no": str(obj.user.mobile_no) if obj.user.mobile_no else None,
        }