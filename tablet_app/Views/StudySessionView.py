from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.serializers import StudySessionSerializer
from tablet_app.models import StudySession

class StudySessionAPI(APIView):

    def get(self, request, pk=None):
        """Get all study sessions or a specific study session by ID"""
        try:
            if pk:
                queryset = StudySession.objects.get(id=pk)
                serializer = StudySessionSerializer(queryset)
                return Response({
                    'status': True,
                    'data': serializer.data,
                    'message': 'Study session retrieved successfully'
                }, status=status.HTTP_200_OK)

            queryset = StudySession.objects.all()
            serializer = StudySessionSerializer(queryset, many=True)
            return Response({
                'status': True,
                'data': serializer.data,
                'message': 'Study sessions listed successfully'
            }, status=status.HTTP_200_OK)

        except StudySession.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Study session not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    
    def post(self, request):
        """Create a new study session"""
        try:
            serializer = StudySessionSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'data': serializer.data,
                    'message': 'Study session created successfully'
                }, status=status.HTTP_201_CREATED)

            return Response({
                'status': False,
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

    def patch(self, request, pk):
        """Update a study session"""
        try:
            queryset = StudySession.objects.get(id=pk)

        except StudySession.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Study session not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = StudySessionSerializer(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': True,
                'data': serializer.data,
                'message': 'Study session updated successfully'
            }, status=status.HTTP_200_OK)

        return Response({
            'status': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        """Delete a study session"""
        try:
            queryset = StudySession.objects.get(id=pk)

        except StudySession.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Study session not found'
            }, status=status.HTTP_404_NOT_FOUND)

        queryset.delete()
        return Response({
            'status': True,
            'message': 'Study session deleted successfully'
        }, status=status.HTTP_200_OK)
