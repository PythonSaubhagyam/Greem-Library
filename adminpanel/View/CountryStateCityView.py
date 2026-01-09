from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from user_management.models import *
from ..serializers import *
import requests



class CountriesAPI(APIView):
    def get(self,request,id=None):
        if id:
            countries = CountryModel.objects.filter(pk=id)
            serializer = CountriesSerializer(countries, many = True)
            return Response({'status': True, 'data':serializer.data,'message':'Countries successfully fetched'},status=status.HTTP_200_OK)
        countries = CountryModel.objects.all()
        serializer = CountriesSerializer(countries, many=True)
        return Response({'status': True, 'data':serializer.data,'message':'Country successfully fetched'},status=status.HTTP_200_OK)    

class StatesAPI(APIView):
    def get(self,request,id=None):
        if id:
            states = StatesModel.objects.filter(country=id)
            serializer = StateSerializer(states, many = True)
            return Response({'status': True, 'data':serializer.data,'message':'States successfully fetched'},status=status.HTTP_200_OK)
        states = StatesModel.objects.all()
        serializer = StateSerializer(states, many = True)
        return Response({'status': True, 'data':serializer.data,'message':'States successfully fetched'},status=status.HTTP_200_OK)
    
class CitiesAPI(APIView):
    def get(self,request,id=None):
        if id:
            cities = CitiesModel.objects.filter(state=id).order_by('name')
            serializer = CitiesSerializer(cities, many = True)
            return Response({'status': True, 'data':serializer.data,'message':'Cities successfully fetched'},status=status.HTTP_200_OK)
        cities = CitiesModel.objects.all()
        serializer = CitiesSerializer(cities, many = True)
        return Response({'status': True, 'data':serializer.data,'message':'Cities successfully fetched'},status=status.HTTP_200_OK)