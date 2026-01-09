from rest_framework import serializers
from user_management.models import *



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
    
    def get_full_name(self,obj):
        if obj.first_name or obj.last_name:
            return f'{obj.first_name} {obj.last_name}'
    
    class Meta:
        model = UserModel
        fields = ['id','full_name','email','mobile_no','date_joined']
        
        
class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserModel
        fields = '__all__'