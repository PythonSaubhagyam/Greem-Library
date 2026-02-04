from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.serializers import StudentTestAttemptSerializer
from tablet_app.models import StudentTestAttemptModel

class StudentTestAttemptAPI(APIView):

    def post(self, request):
        try:
            serializer = StudentTestAttemptSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(
                    student = request.user,
                    score = 0,
                    is_completes = False,
                    completed_at = None
                )
                return Response({'status': True, 'data': serializer.data, 'message': 'Student test attempted successfully'}, status=status.HTTP_200_OK)
            
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def get(self, request, pk=None):
        try:
            if pk:
                queryset = StudentTestAttemptModel.objects.get(id=pk)
                serializer = StudentTestAttemptSerializer(queryset)
                return Response({'status': True, 'data': serializer.data, 'message': 'Which student attempt test that student listed successfully'}, status=status.HTTP_200_OK)
            
            queryset = StudentTestAttemptModel.objects.all()
            serializer = StudentTestAttemptSerializer(queryset, many=True)
            return Response({'status': True, 'data': serializer.data, 'message': 'which student attept test that student listed successfully'}, status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request, pk):
        try:
            queryset = StudentTestAttemptModel.objects.get(id=pk)

        except StudentTestAttemptModel.DoesNotExist:
            return Response({'status': False, 'message': 'Student test attempt not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StudentTestAttemptSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
        return Response({'status': True, 'data': serializer.data, 'message': 'student test attempt updated successfully'}, status=status.HTTP_200_OK)
    

    def delete(self, request, pk):
        try:
            queryset = StudentTestAttemptModel.objects.get(id=pk)

        except StudentTestAttemptModel.DoesNotExist:
            return Response({'status': False, 'message': 'Student test attempted not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset.delete()
        return Response({'status': False, 'message': 'Student test attempted deleted successfully'}, status=status.HTTP_200_OK)