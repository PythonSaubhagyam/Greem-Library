from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import TabletLeadFollowUpModel
from adminpanel.serializers import TabletLeadFollowUpSerializer


class TabletLeadFollowUpAPI(APIView):

    def get(self, request, pk=None):
        try:
            if pk:
                queryset = TabletLeadFollowUpModel.objects.get(id=pk)
                serializer = TabletLeadFollowUpSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Tablet lead follow up retrieve successfully'}, status=status.HTTP_200_OK)
            
            queryset = TabletLeadFollowUpModel.objects.all()
            serializer = TabletLeadFollowUpSerializer(queryset, many=True)
            return Response({'status': True, 'data': serializer.data, 'message': 'Tablet lead follow up listed successfully'}, status=status.HTTP_200_OK)
        
        except TabletLeadFollowUpModel.DoesNotExist:
            return Response({'status': False, 'message': 'Tablet lead follow up not found'}, status=status.HTTP_404_NOT_FOUND)
        

    def post(self, request):
        try:
            serializer = TabletLeadFollowUpSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'Tablet lead follow up created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
    def patch(self, request, pk):
        try:
            queryset = TabletLeadFollowUpModel.objects.get(id=pk)

        except TabletLeadFollowUpModel.DoesNotExist:
            return Response({'status': False, 'message': 'Tablet lead follow up not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TabletLeadFollowUpSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'Tablet lead follow up updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            queryset = TabletLeadFollowUpModel.objects.get(id=pk)

        except TabletLeadFollowUpModel.DoesNotExist:
            return Response({'status': False, 'message': 'Tablet lead follow up not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset.delete()
        return Response({'status': True, 'message': 'Tablet lead follow up deleted successfully'}, status=status.HTTP_200_OK)