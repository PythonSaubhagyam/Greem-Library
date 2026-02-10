from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.serializers import pdfGroupSerializer
from tablet_app.models import pdfGroupModel
from adminpanel.pagination import ListPagination


class pdfGroupAPI(APIView):
    pagination_class = ListPagination


    def get(self, request, pk=None):
        try:
            if pk:
                queryset = pdfGroupModel.objects.get(id=pk)
                serializer = pdfGroupSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'pdf Group retrieve successfully'}, status=status.HTTP_200_OK)

            queryset = pdfGroupModel.objects.all().order_by('-id')

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = pdfGroupSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        except pdfGroupModel.DoesNotExist:
            return Response({'status': False, 'message': 'Pdf group not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, *args, **kwargs):
        try:
            serializer = pdfGroupSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'pdf Group created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request, pk):
        try:
            queryset = pdfGroupModel.objects.get(id=pk)

        except pdfGroupModel.DoesNotExist:
            return Response({'status': False, 'message': 'Pdf group not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = pdfGroupSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'pdf Group updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        
    def delete(self, request, pk):
        try:
            queryset = pdfGroupModel.objects.get(id=pk)

        except pdfGroupModel.DoesNotExist:
            return Response({'status': False, 'message': 'Pdf group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset.delete()
        return Response({'status': True, 'message': 'pdf Group deleted successfully'}, status=status.HTTP_200_OK)

        