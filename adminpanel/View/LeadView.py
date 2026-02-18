from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import TabletLeadModel
from adminpanel.serializers import TabletLeadSerializer
from django.db.models import Q


class LeadAPI(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                queryset = TabletLeadModel.objects.get(id=pk)
                serializer = TabletLeadSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Lead retrieve successfully'}, status=status.HTTP_200_OK)
            
            q = request.GET.get('q', '').strip()
            queryset = TabletLeadModel.objects.all()

            if q:
                queryset = queryset.filter(
                    Q(name__icontains=q) |
                    Q(mobile__icontains=q) |
                    Q(email__icontains=q) |
                    Q(customer_type__icontains=q) |
                    Q(school_name__icontains=q) |
                    Q(tablet_model__icontains=q) |
                    Q(tablet_variant__icontains=q)|
                    Q(quantity__icontains=q)|
                    Q(price_per_unit__icontains=q)|
                    Q(total_price__icontains=q)|
                    Q(demo_required__icontains=q)|
                    Q(demo_done__icontains=q)|
                    Q(stage__icontains=q)|
                    Q(payment_status__icontains=q)
                )

                
            serializer = TabletLeadSerializer(queryset, many=True)
            return Response({'status': True, 'data': serializer.data, "count": queryset.count(), 'message': 'Lead listed successfully'}, status=status.HTTP_200_OK)

        except TabletLeadModel.DoesNotExist:
            return Response({'status': False, 'message': 'Tablet lead not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def post(self, request):
        try:
            serializer = TabletLeadSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'Lead created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, pk):
        try:
            queryset = TabletLeadModel.objects.get(id=pk)
            
        except TabletLeadModel.DoesNotExist:
            return Response({'status': False, 'message': 'Tablet lead not found'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = TabletLeadSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'Tablet lead updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        try:
            queryset = TabletLeadModel.objects.get(id=pk)

        except TabletLeadModel.DoesNotExist:
            return Response({'status': False, 'message': 'Tablet lead not fount'}, status=status.HTTP_404_NOT_FOUND)
    
        queryset.delete()
        return Response({'status': True, 'message': 'Tablet lead deleted successfully'}, status=status.HTTP_200_OK)