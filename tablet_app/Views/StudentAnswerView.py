from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.serializers import StudentAnswerSerializer
from tablet_app.models import StudentAnswerModel
from adminpanel.pagination import ListPagination


class StudentAnswerAPI(APIView):
    pagination_classes = ListPagination

    def post(self, request, *args, **kwargs):
        try:
            serializer = StudentAnswerSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'Student answer create successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def get(self, request, pk=None):
        try:
            if pk:
                queryset = StudentAnswerModel.objects.get(id=pk)
                serializer = StudentAnswerSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Student answer retrieve successflly'}, status=status.HTTP_200_OK)
            
            queryset = StudentAnswerModel.objects.all().order_by('-id')

            paginator = self.pagination_classes()
            paginated_queryset  = paginator.paginate_queryset(queryset, request)

            serializer = StudentAnswerSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except StudentAnswerModel.DoesNotExist:
            return Response({'status': False, 'message': 'Student answer not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request, pk):
        try:
            queryset = StudentAnswerModel.objects.get(id=pk)
        
        except StudentAnswerModel.DoesNotExist:
            return Response({'status': False, 'message': 'Student answer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StudentAnswerSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'Student answer updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def delete(self, request, pk):
        try:
            queryset = StudentAnswerModel.objects.get(id=pk)

        except StudentAnswerModel.DoesNotExist:
            return Response({'status': False, 'message': 'Student answer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset.delete()
        return Response({'status': True, 'message': 'Student answer deleted successfully'}, status=status.HTTP_200_OK)
        
        