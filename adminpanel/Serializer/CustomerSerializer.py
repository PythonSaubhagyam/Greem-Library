from rest_framework import serializers
from user_management.models import *
from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField
from ..serializers import UserSerializer

class CustomerDetailSerializer(serializers.ModelSerializer):

    customer_name = serializers.SerializerMethodField()
    # email = serializers.EmailField(source='user.email', read_only=True)
    # mobile_no = serializers.CharField(source='user.mobile_no', read_only=True)
    phone_no = serializers.CharField(source='mobile_no.national_number', read_only=True)
    # first_name = serializers.CharField(source='user.first_name', read_only=True)
    # last_name = serializers.CharField(source='user.last_name', read_only=True)
    devices = serializers.SerializerMethodField()

    def get_devices(self, obj):
        details = []
        devices = obj.devicemodel_set.all()
        for device in devices:
            details.append({
                'imei_number': device.imei_number,
                'Active': "Yes" if device.is_active else "No",
            })
        return details

    def get_customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    class Meta:
        model = UserModel
        fields = [
            "id",
            "email",
            "customer_name",
            "mobile_no",
            "phone_no",
            "first_name",
            "last_name",
            "devices"
        ]

    def validate_imei_number(self, value):

        if DeviceModel.objects.filter(imei_number=value).exists():
            raise serializers.ValidationError("This IMEI already exists.")

        return value

class DeviceCreateUpdateSerializer(serializers.ModelSerializer):

    def validate_imei_number(self, value):
        print(value,'valuevaluevaluevalue')

        if DeviceModel.objects.filter(imei_number=value).exists():
            print('exists')
            raise serializers.ValidationError("This IMEI already exists.")

        return value

    class Meta:
        model = DeviceModel
        fields = ["id","user","imei_number"]
    
        

class DeviceMiniSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    def get_status(self, obj):
        return "Active" if obj.is_active else "In Active"


    def get_customer_name(self, obj):   
        return f"{obj.user.first_name} {obj.user.last_name}"

    class Meta:
        model = DeviceModel
        fields = [
            "id",
            "imei_number",
            "is_active",
            "status",
            "user",
            "customer_name",
            "email"
        ]

class CustomerCreateUpdateSerializer(serializers.Serializer):

    # ---- USER FIELDS ----
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    mobile_no = serializers.CharField(required=False, allow_blank=True)

    # password = serializers.CharField(required=False, write_only=True)

    # ---- ADDRESS (passed via context) ----
    address_text = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    city = serializers.IntegerField(required=False)
    state = serializers.IntegerField(required=False)
    country = serializers.IntegerField(required=False)
    # password = serializers.CharField(required=False, write_only=True, allow_blank=True)
    # ---- DEVICES ----
    # devices = DeviceCreateUpdateSerializer(many=True)

    # --------------------------------------------------
    # def validate_devices(self, devices):

    #     imeis = [d["imei_number"] for d in devices]

    #     # ---- duplicate inside payload ----
    #     if len(imeis) != len(set(imeis)):
    #         raise serializers.ValidationError(
    #             "Duplicate IMEI numbers in request."
    #         )

    #     # ---- DB check ----
    #     qs = DeviceModel.objects.filter(imei_number__in=imeis)

    #     # UPDATE → allow user's own devices
    #     if self.instance:
    #         user = self.instance
    #         qs = qs.exclude(user=user)

    #     if qs.exists():
    #         raise serializers.ValidationError(
    #             "One or more IMEIs already exist."
    #         )

    #     return devices

    def create(self, validated_data):
        print(validated_data,'validated_datavalidated_datavalidated_data')

        # devices_data = validated_data.pop("devices")
        validated_data['role'] = RoleModel.objects.filter(type="Customer").first().id

        if not validated_data.get('username'):
           validated_data['username'] = validated_data.get('email')

        # if not validated_data.get('password'):
        #     mobile = str(validated_data.get('mobile_no', '')).replace('+91', '').strip()
        #     validated_data['password'] = mobile

        # ---- CREATE USER USING YOUR EXISTING SERIALIZER ----
        user_serializer = UserSerializer(
            data=validated_data,
            context={
                "request": self.context.get("request"),
                "address_text": validated_data.get("address_text"),
                "postal_code": validated_data.get("postal_code"),
                "city": validated_data.get("city"),
                "state": validated_data.get("state"),
                "country": validated_data.get("country"),
            }
        )

        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # ---- CREATE DEVICES ----
        # devices = []

        # for d in devices_data:
        #     devices.append(
        #         DeviceModel(
        #             user=user,
        #             imei_number=d["imei_number"]
        #         )
        #     )

        # DeviceModel.objects.bulk_create(devices)

        return user

    # --------------------------------------------------

    def update(self, instance, validated_data):
        # print(validated_data['devices'],'--------------------')
        # devices_data = validated_data.pop("devices", [])

        # ---- UPDATE USER ----
        user_serializer = UserSerializer(
            instance,
            data=validated_data,
            partial=True,
            context={
                "request": self.context.get("request"),
                "address_text": validated_data.get("address_text"),
                "postal_code": validated_data.get("postal_code"),
                "city": validated_data.get("city"),
                "state": validated_data.get("state"),
                "country": validated_data.get("country"),
            }
        )

        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # ---- SYNC DEVICES ----

        # existing = DeviceModel.objects.filter(user=user)
        # existing_map = {d.imei_number: d for d in existing}

        # incoming_imeis = []

        # for d in devices_data:

        #     imei = d["imei_number"]
        #     incoming_imeis.append(imei)

        #     if imei in existing_map:
        #         continue
        #     else:
        #         DeviceModel.objects.create(
        #             user=user,
        #             imei_number=imei
        #         )
        
        

        # # ---- REMOVE DELETED DEVICES ----
        # existing.exclude(imei_number__in=incoming_imeis).delete()


        return user
