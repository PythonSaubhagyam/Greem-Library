from rest_framework import serializers
from user_management.models import *
from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField



class CountriesSerializer(serializers.ModelSerializer):

    all_state = serializers.SerializerMethodField(read_only=True)

    def get_all_state(self, obj):
        get_all_country = StatesModel.objects.filter(country=obj).values()
        return get_all_country

    class Meta:
        model = CountryModel
        fields = ['id','country_name','country_code','currency','calling_code', 'all_state']


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.SerializerMethodField(read_only=True)
    all_cities = serializers.SerializerMethodField(read_only=True)

    def get_all_cities(self, obj):
        get_all_cities = CitiesModel.objects.filter(state=obj).values()
        return get_all_cities

    def get_country_name(self, obj):
        return obj.country.country_name

    class Meta:
        model = StatesModel
        fields = ['id','country','country_name','name','all_cities']


class CitiesSerializer(serializers.ModelSerializer):
    state_name = serializers.SerializerMethodField(read_only=True)
    country_name = serializers.SerializerMethodField(read_only=True)

    def get_state_name(self, obj):
        return obj.state.name

    def get_country_name(self, obj):
        return obj.country.country_name


    class Meta:
        model = CitiesModel
        fields = ['id','country','country_name','state','state_name','name']
        
class UsersListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format="%d-%m-%Y at %H:%M:%S", read_only=True)
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    city_id = serializers.SerializerMethodField()
    state_id = serializers.SerializerMethodField()
    country_id = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    postal_code = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    country_code = serializers.SerializerMethodField()

    def get_phone_no(self, obj):
        if obj.mobile_no:
            return obj.mobile_no.national_number
        return None
    
    def get_country_code(self, obj):
        if obj.mobile_no:
            return obj.mobile_no.country_code
        return None

    def get_default_address(self, obj):
        return obj.address.filter(is_default=True).first()
    
    def get_postal_code(self, obj):
        addr = self.get_default_address(obj)
        return addr.postal_code if addr else None

    def get_city(self, obj):
        addr = self.get_default_address(obj)
        return addr.city if addr else None

    def get_state(self, obj):
        addr = self.get_default_address(obj)
        return addr.state if addr else None

    def get_country(self, obj):
        addr = self.get_default_address(obj)
        return addr.country if addr else None

    def get_city_id(self, obj):
        addr = self.get_default_address(obj)
        return addr.fcity.id if addr and addr.fcity else None

    def get_state_id(self, obj):
        addr = self.get_default_address(obj)
        return addr.fstate.id if addr and addr.fstate else None

    def get_country_id(self, obj):
        addr = self.get_default_address(obj)
        return addr.fcountry.id if addr and addr.fcountry else None

    def get_address(self, obj):
        addr = self.get_default_address(obj)
        return str(addr.address) if addr else None

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_role_name(self, obj):
        return obj.role.type if obj.role else None
    
    class Meta:
        model = UserModel
        fields = [
            "id","full_name","first_name","last_name","email","mobile_no",
            "date_joined","address",
            "city","state","country",
            "city_id","state_id","country_id","postal_code","role_name","phone_no","country_code"
        ]
        
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True, "required": False, "allow_blank": True},
            "address": {"read_only": True},   # CRITICAL FIX
        }

    def create(self, validated_data):
        print(validated_data,'-----------')
        request = self.context.get("request")
        password = validated_data.pop("password", None)

        user = UserModel.objects.create(**validated_data)

        if password:
            user.set_password(password)
            user.save()

        self.save_address(user)
        return user

    def update(self, instance, validated_data):
        print(validated_data,'---------')
        for k, v in validated_data.items():
            setattr(instance, k, v)

        instance.save()
        self.save_address(instance)
        return instance

    def save_address(self, user):
        address_text = self.context.get("address_text")
        postal_code = self.context.get("postal_code")
        city_id = self.context.get("city")
        state_id = self.context.get("state")
        country_id = self.context.get("country")

        if not address_text:
            return

        city = CitiesModel.objects.get(id=city_id) if city_id else None
        state = StatesModel.objects.get(id=state_id) if state_id else None
        country = CountryModel.objects.get(id=country_id) if country_id else None

        AddressModel.objects.filter(is_default=True).update(is_default=False)

        address = AddressModel.objects.create(
            address=address_text,
            postal_code=postal_code,
            fcity=city,
            fstate=state,
            fcountry=country,
            is_default=True
        )

        user.address.add(address)


class StudentsSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    # parent_name = serializers.SerializerMethodField()
    # teacher_name = serializers.SerializerMethodField()

    # def get_parent_name(self, obj):
    #     parents = []
    #     if obj.parent.exists():
    #         for parent in obj.parent.all():
    #             if parent.role.type == 'Parent':
    #                 parents.append(f"{parent.first_name} {parent.last_name}")
    #         return parents

    #     return ''
    
    # def get_teacher_name(self, obj):
    #     teachers = []
    #     if obj.parent.exists():
    #         for parent in obj.parent.all():
    #             if parent.role.type == 'Teacher':
    #                 teachers.append(f"{parent.first_name} {parent.last_name}")
    #         return teachers
                
    #     return ''

    def get_customer_name(self, obj):
        if obj.parent.exists():
            for parent in obj.parent.all():
                if parent.role.type == 'Customer':
                    return f"{parent.first_name} {parent.last_name}"
        return ''
    
    def create(self, validated_data):
        request = self.context.get("request")
        parent_ids = request.data.get("parent", [])
        print(parent_ids,'parent_idsparent_idsparent_ids')
        student = super().create(validated_data)
        # if parent_ids:
        #     parents = UserModel.objects.filter(id__in=parent_ids)
        #     student.parent.set(parents)
        return student
    
    def update(self, instance, validated_data):
        parents = validated_data.get("parent", None)
        print(parents,'parentsparentsparents')
        instance = super().update(instance, validated_data)
        # if parents is not None:
        #     instance.parent.set(parents)
        return instance 

    class Meta:
        model = StudentModel
        fields = ['id', 'student_id','student_name', 'email','parent','customer_name','student_class']

class EmployeeCreateSerializer(serializers.ModelSerializer):

    # ---- USER FIELDS ----
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    mobile_no = PhoneNumberField(required=False, allow_null=True)
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
            "mobile_no": obj.user.mobile_no.national_number if obj.user.mobile_no else None,
        }

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

        

        fields = ['id', 'student_id','student_name', 'email','parent','parent_name','teacher_name','student_class']



class TabletLeadSerializer(serializers.ModelSerializer):

    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset = UserModel.objects.all(),
        source = 'created_by',
        write_only = True,
        required = False
    )
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset = EmployeeModel.objects.all(),
        source = 'assigned_to',
        write_only = True,
        required = False
    )

    created_by = serializers.StringRelatedField(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)

    comment = serializers.CharField(default="", allow_blank=True)


    class Meta:
        model = TabletLeadModel
        fields = (
            'id', 'name', 'mobile', 'email', 'customer_type', 'school_name', 'tablet_model', 'tablet_variant', 'quantity', 'price_per_unit',
            'total_price', 'demo_required', 'demo_done', 'demo_date', 'stage', 'payment_status', 'delivery_date', 'created_by_id', 'created_by',
            'assigned_to_id', 'assigned_to', "comment", 'is_deleted', 'created_at', 'updated_at'
        )


class TabletLeadFollowUpSerializer(serializers.ModelSerializer):

    tablet_lead_id = serializers.PrimaryKeyRelatedField(
        queryset = TabletLeadModel.objects.all(),
        source = 'tablet_lead',
        write_only = True
    )
    followup_by_id = serializers.PrimaryKeyRelatedField(
        queryset = UserModel.objects.all(),
        source = 'followup_by',
        write_only = True
    )

    tablet_lead = serializers.StringRelatedField(read_only=True)
    followup_by = serializers.StringRelatedField(read_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = TabletLeadFollowUpModel
        fields = (
            'id', 'tablet_lead_id', 'tablet_lead', 'followup_type', 'followup_date', 'comment', 'followup_by_id', 'followup_by',
            'stage_update', 'next_followup_date', 'created_at'
        )
