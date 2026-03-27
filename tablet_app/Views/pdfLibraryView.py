from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from tablet_app.serializers import *
from adminpanel.pagination import ListPagination


class pdfLibraryAPI(APIView):
    # permission_classes = [IsAuthenticated]
    pagination_classes = ListPagination

    def get(self, request, pk=None):
        try:

            group_id = request.query_params.get('group_id')

            if pk:
                queryset = pdfLibraryModel.objects.get(id=pk, student=request.user)
                serializer = pdfLibrarySerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'pdf library retrieve successfully'}, status=status.HTTP_200_OK)

            queryset = pdfLibraryModel.objects.filter(student=request.user).order_by('-id')

            if group_id:
                queryset = pdfLibraryModel.objects.filter(group__id = group_id).order_by('-id')

            # queryset = pdfLibraryModel.objects.all().order_by('-id')

            paginator = self.pagination_classes()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = pdfLibrarySerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except pdfLibraryModel.DoesNotExist:
            return Response({'status': False, 'message': 'Pdf library not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
    def post(self, request):
        try:
            serializer = pdfLibrarySerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'pdf Library created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def patch(self, request, pk):
        try:
            queryset = pdfLibraryModel.objects.get(id=pk)
        
        except pdfLibraryModel.DoesNotExist:
            return Response({'status': False, 'message': 'Pdf library not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = pdfLibrarySerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'pdf Library updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    
    def delete(self, request, pk):
        try:
            object = pdfLibraryModel.objects.get(id=pk)

        except pdfLibraryModel.DoesNotExist:
            return Response({'status': False, 'message': 'Pdf library not found'}, status=status.HTTP_404_NOT_FOUND)
        
        object.delete()
        return Response({'status': True, 'message': 'pdf Library deleted successfully'}, status=status.HTTP_200_OK)
        

class StudentpdfListAPI(APIView):
    def get(self, request, student_id):
        pdf = pdfLibraryModel.objects.filter(student_id=student_id)
        serializer = pdfLibrarySerializer(pdf,many=True)
        return Response(serializer.data)