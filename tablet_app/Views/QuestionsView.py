from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.models import QuestionsModel
from tablet_app.serializers import QuestionsSerializer
from adminpanel.pagination import ListPagination

class QuestionsAPI(APIView):
    pagination_classes = ListPagination

    def post(self, request):
        try:
            serializer = QuestionsSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'Question created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def get(self, request, pk=None):
        try:
            if pk:
                queryset = QuestionsModel.objects.get(id=pk)
                serializer = QuestionsSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Question retrieve successfully'}, status=status.HTTP_200_OK)
            
            queryset = QuestionsModel.objects.all().order_by('-id')

            paginator = self.pagination_classes()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = QuestionsSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        except QuestionsModel.DoesNotExist:
            return Response({'status': False, 'message': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request, pk):
        try:
            queryset = QuestionsModel.objects.get(id=pk)

        except QuestionsModel.DoesNotExist:
            return Response({'status': False, 'message': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = QuestionsSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'Question updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def delete(self, request, pk):
        try: 
            quesryset = QuestionsModel.objects.get(id=pk)
        
        except QuestionsModel.DoesNotExist:
            return Response({'status': False, 'message': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
        
        quesryset.delete()
        return Response({'status': True, 'message': 'Question deleted sucessfully'}, status=status.HTTP_200_OK)