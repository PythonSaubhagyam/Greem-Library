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

