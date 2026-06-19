from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.models import Subject
from adminpanel.Serializer.SubjectSerializer import SubjectSerializer
from adminpanel.pagination import ListPagination


class SubjectAPI(APIView):

    def get(self, request):
        subjects = Subject.objects.all().order_by('name')
        paginator = ListPagination()
        page = paginator.paginate_queryset(subjects, request)
        serializer = SubjectSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.save()
            return Response({
                'data': SubjectSerializer(subject).data,
                'message': 'Subject created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SubjectSerializer(subject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Updated successfully'})
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
            subject.delete()
            return Response({'message': 'Deleted successfully'})
        except Subject.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


from adminpanel.views import DashboardsView

class SubjectView(DashboardsView):
    template_name = "subjects_list.html"