from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from rest_framework.permissions import IsAuthenticated
from ..pagination import ListPagination
from django.utils import timezone
from datetime import timedelta
 
class UserAPIView(APIView):
    # permission_classes = [IsAuthenticated]
 
    def get(self, request):
        # company_id = request.GET.get('id')
        country=request.GET.get('country', None)
        state = request.GET.get('state', None)
        city = request.GET.get('city', None)
        user = request.GET.get('user', None)
        type1 = request.GET.get('type', None)
        parentteacher = request.GET.get('parentteacher', None)
        q = request.GET.get('q', '').strip()  # get search query
        status= request.query_params.get('status', '')
        user_id = request.GET.get('id')
        users = UserModel.objects.filter(is_active=True).order_by('-id').exclude(role__type='Admin')
        if user_id:
            users = users.filter(id=user_id)
        if type1:
            users = users.filter(role__type__icontains=type1)
        if parentteacher:
            if parentteacher == 'customer':
                users = users.filter(Q(role__type__in=['Customer']))
        # if country:
        #     country_name = CountryModel.objects.get(id=country)
        #     companies = companies.filter(user__country__iexact=country_name.country_name)
        # if state:
        #     state_name = StatesModel.objects.get(id=state)
        #     companies = companies.filter(user__state__iexact=state_name.name)
        # if city:
        #     city_name = CitiesModel.objects.get(id=city)
        #     companies = companies.filter(user__city__iexact=city_name.name)
       
        if user is not None:
            if user == 'parents':
               users = users.filter(role__type='Parent')
            elif user == 'teachers':
                users = users.filter(role__type='Teacher')
            
        
        # if status:
        #     three_months_ago = timezone.now() - timedelta(days=90)
        #     active_company_ids = []
        #     in_active_company_ids = []
        #     for company in companies:
        #         company_user = company.user
        #         last_active_obj = (
        #             Conversation.objects.filter(user=company_user)
        #             .order_by('-last_active')
        #             .first()
        #         )
        #         if last_active_obj and last_active_obj.last_active:
        #             last_active_time = (
        #                 last_active_obj.last_active
        #                 if timezone.is_aware(last_active_obj.last_active)
        #                 else timezone.make_aware(last_active_obj.last_active)
        #             )
        #             if last_active_time >= three_months_ago:
        #                 active_company_ids.append(company.id)
        #             else:
        #                 in_active_company_ids.append(company.id)
        #         else:
        #             in_active_company_ids.append(company.id)
        #     if status.lower() == 'active':
        #        companies = companies.filter(id__in=active_company_ids)
        #     elif status.lower() == 'inactive':
        #        companies = companies.filter(id__in=in_active_company_ids)
 
        if q:
            users = users.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(mobile_no__icontains=q)
            )
        
        paginator = ListPagination()
        paginated_companies = paginator.paginate_queryset(users,request)
        serializer = UsersListSerializer(paginated_companies, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        data = request.data.copy()

        address_text = data.pop("address", None)
        postal_code = data.pop("postal_code", None)
        city = data.pop("city", None)
        state = data.pop("state", None)
        country = data.pop("country", None)

        role_type = data.get("role_type")

        if role_type:
            try:
                role = RoleModel.objects.get(type__iexact=role_type)
                data["role"] = role.id
            except RoleModel.DoesNotExist:
                return Response({"error": "Invalid role"}, status=400)

        serializer = UserSerializer(
            data=data,
            context={
                "request": request,
                "address_text": address_text,
                "postal_code": postal_code,
                "city": city,
                "state": state,
                "country": country, 
            },
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=201)

        return Response({'errors':serializer.errors}, status=400)

    
    def patch(self, request, id):
        data = request.data.copy()

        address_text = data.pop("address", None)
        postal_code = data.pop("postal_code", None)
        city = data.pop("city", None)
        state = data.pop("state", None)
        country = data.pop("country", None)

        try:
            user = UserModel.objects.get(id=id)
        except UserModel.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = UserSerializer(
            user,
            data=data,
            partial=True,
            context={
                "request": request,
                "address_text": address_text,
                "postal_code": postal_code,
                "city": city,
                "state": state,
                "country": country,
            },
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated successfully"})

        return Response(serializer.errors, status=400)

    
    def delete(self,request,id):
        try:
            user = UserModel.objects.get(id=id)
        except UserModel.DoesNotExist:
            return Response({'error':'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user.is_active = False
        user.save()
        return Response({'message':'User deleted successfully'}, status=status.HTTP_200_OK)  
        
        
        
        
