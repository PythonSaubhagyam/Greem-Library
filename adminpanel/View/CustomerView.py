from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from user_management.models import *
from ..serializers import  *
from ..pagination import ListPagination
from django.db.models import Q

class CustomerViewAPI(APIView):

    def get(self, request, pk=None):
        q = request.GET.get("q")

        if pk is not None:
            try:
                # customer = DeviceModel.objects.select_related("user").get(pk=pk)
                customer = UserModel.objects.prefetch_related("devicemodel_set").get(pk=pk)
                serializer = CustomerDetailSerializer(customer)
                return Response({'status':True,'data':serializer.data,'message':'Customer retrieved successfully'})
            except UserModel.DoesNotExist:
                return Response(
                    {"errors": "Customer not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            customers = UserModel.objects.filter(role__type="Customer").prefetch_related("devicemodel_set").all().order_by("-id")
            if q:
                customers = customers.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(mobile_no__icontains=q)
            )
            paginatior = ListPagination()
            paginated_customers = paginatior.paginate_queryset(customers, request)
            serializer = CustomerDetailSerializer(paginated_customers, many=True)

        return paginatior.get_paginated_response(serializer.data)

    def post(self, request):

        serializer = CustomerCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            customer = serializer.save()
            # devices = DeviceModel.objects.filter(id=customer.id)
            # serializer = DeviceSerializer(devices, many=True)
            return Response({'status':True,'data':CustomerDetailSerializer(customer).data,'message':'Customer created successfully'},status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):

        try:
            customer = UserModel.objects.get(pk=pk)
        except UserModel.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CustomerCreateUpdateSerializer(
            customer,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            customer = serializer.save()
            # devices = DeviceModel.objects.filter(id=customer.id)
            # serializer = DeviceSerializer(devices, many=True)
            return Response({'status':True,'data':CustomerDetailSerializer(customer).data,'message':'Customer updated successfully'})

        return Response({"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        try:
            customer = UserModel.objects.get(pk=pk)
        except UserModel.DoesNotExist:
            return Response(
                {"error": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        
        customer.devicemodel_set.all().delete()
        customer.delete()

        return Response(
            {"message": "Customer deleted successfully"}
        )

class CustomerDeviceAPI(APIView):

    def get(self, request, pk=None):

        q = request.GET.get("q", "")
        customer_id = request.GET.get("customer")

        if pk is not None and not customer_id:
            qs = DeviceModel.objects.filter(id=pk).first()
            print(qs)
            serializer = DeviceMiniSerializer(qs)
            return Response({'status':True,"data": {"device": serializer.data,"user": qs.user.id,"customer_name": f'{qs.user.first_name} {qs.user.last_name}'},'message':'Devices retrieved successfully'})
        
        else:
            qs = DeviceModel.objects.all().order_by('-id')
        
        if customer_id:
           qs = qs.filter(user_id=customer_id)

        if q:
            q_lower = q.lower()

            bool_value = None

            if q_lower in ['a', 'ac', 'act', 'activ', 'active', 'true', '1']:
                bool_value = True
            elif q_lower in ['i', 'in', 'ina', 'inac','in ac', 'inact', 'inacti', 'inactiv', 'inactive', 'false', '0']:
                bool_value = False

            filters = Q(imei_number__icontains=q)| Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__email__icontains=q)

            if bool_value is not None:
                filters |= Q(is_active=bool_value)

            qs = qs.filter(filters)

        paginator = ListPagination()
        
        if customer_id:
            paginator.page_size = 10  

        page = paginator.paginate_queryset(qs, request)

        serializer = DeviceMiniSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
    

    def post(self, request):
        customer_devices = request.data.get("devices", [])
        for device in customer_devices:
            device['user'] = request.data.get("user")
        print(customer_devices,'customer_devicescustomer_devicescustomer_devices')
        serializer = DeviceCreateUpdateSerializer(data=customer_devices,many=True)

        if serializer.is_valid():
            device = serializer.save()
            print(device,'devicedevicedevice')
            return Response({
                "status": True,
                "data": DeviceMiniSerializer(device,many=True).data,
                "message": "Device created successfully"
            }, status=status.HTTP_201_CREATED)

        return Response({"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)
       
    
    def patch(self, request, pk):

        try:
            device = DeviceModel.objects.get(pk=pk)
        except DeviceModel.DoesNotExist:
            return Response(
                {"error": "Device not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DeviceCreateUpdateSerializer(
            device,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Device updated successfully"
            })

        return Response({"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):

        try:
            device = DeviceModel.objects.get(pk=pk)
        except DeviceModel.DoesNotExist:
            return Response(
                {"error": "Device not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        device.delete()

        return Response(
            {"message": "Device deleted successfully"}
        )