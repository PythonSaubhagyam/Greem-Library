from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from user_management.models import StudentModel
from adminpanel.serializers import StudentsSerializer


class ParentChildListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.role or user.role.type != 'Parent':
            return Response({'status': False, 'message': 'Only parent can view child'}, status=status.HTTP_403_FORBIDDEN)
        
        student = StudentModel.objects.filter(parent=user)
        serializer = StudentsSerializer(student, many=True, context={"request": request})

        return Response({'status': True, 'data': serializer.data}, status=status.HTTP_200_OK)