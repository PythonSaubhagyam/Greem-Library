from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.serializers import QuestionOptionsSerializer
from tablet_app.models import QuestionOptionsModel

class QuestionOptionsAPI(APIView):

    def post(self, request):
        try:
            serializer = QuestionOptionsSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'data': serializer.data, 'message': 'Option created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def get(self, request, pk=None):
        try:
            question_id = request.query_params.get('question_id')
            
            if pk:
                queryset = QuestionOptionsModel.objects.get(id=pk)
                serializer = QuestionOptionsSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Question options retrieve successfully'}, status=status.HTTP_200_OK)
            
            if question_id:
                queryset = QuestionOptionsModel.objects.filter(question_id=question_id)
                serializer = QuestionOptionsSerializer(queryset, many=True)
                return Response({'status': True, 'data': serializer.data, 'message': 'Question options retrieve successfully'}, status=status.HTTP_200_OK)
            
            queryset = QuestionOptionsModel.objects.all()
            serializer = QuestionOptionsSerializer(queryset, many=True)
            return Response({'status': True, 'data': serializer.data, 'message': 'Question Options listed successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request, pk):
        try:
            option = QuestionOptionsModel.objects.get(id=pk)

        except QuestionOptionsModel.DoesNotExist:
            return Response({'status': False, 'message': 'Question option not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = QuestionOptionsSerializer(option, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data, 'message': 'Question option updated successfully'}, status=status.HTTP_200_OK)
        return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)        


    def delete(self, request, pk):
        try:
            option = QuestionOptionsModel.objects.get(id=pk)

        except QuestionOptionsModel.DoesNotExist:
            return Response({'status': False, 'message': 'Question option not found'}, status=status.HTTP_404_NOT_FOUND)
        
        option.delete()
        return Response({'status': True, 'message': 'Question option deleted successfully'}, status=status.HTTP_200_OK)