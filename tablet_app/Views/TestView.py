from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.serializers import TestSerializer
from tablet_app.models import TestModel
from adminpanel.pagination import ListPagination


class TestAPI(APIView):
    pagination_class = ListPagination

    def post(self, reqeust, *args, **kwargs):
        try:
            serializer = TestSerializer(data=reqeust.data, context={'request': reqeust})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'Test created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def get(self, request, pk=None):
        try:
            if pk:
                queryset = TestModel.objects.get(id=pk)
                serializer = TestSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Test retrieve successfully'}, status=status.HTTP_200_OK)
            
            queryset = TestModel.objects.all().order_by('-id')

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = TestSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except TestModel.DoesNotExist:
            return Response({'status': False, 'message': 'Test not found'}, status=status.HTTP_404_NOT_FOUND)
                
    
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def patch(self, request, pk):
        try:
            queryset = TestModel.objects.get(id=pk)
        
        except TestModel.DoesNotExist:
            return Response({'status': False, 'message': 'Test not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TestSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'Test updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
      
    def delete(self, request, pk):
        try:
            queryset = TestModel.objects.get(id=pk)
        
        except TestModel.DoesNotExist:
            return Response({'status': False, 'message': 'Test not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset.delete()
        return Response({'status': True, 'message': 'Test deleted suceessfully'}, status=status.HTTP_200_OK)