from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator

from adminpanel.Serializer.ClassSerializer import ClassSerializer

try:
    from user_management.models import ClassModel
except Exception:
    ClassModel = None


class ClassAPIView(APIView):
    """List and create ClassModel instances."""

    def get(self, request, pk=None):
        if ClassModel is None:
            return Response({'error': 'ClassModel not available'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        qs = ClassModel.objects.all().order_by('-created_at')

        # Optional filters
        standard = request.GET.get('standard')
        academic_year = request.GET.get('academic_year')
        if standard and standard.isdigit():
            qs = qs.filter(standard=int(standard))
        if academic_year:
            qs = qs.filter(academic_year__iexact=academic_year)

        if pk:
            try:
                obj = qs.get(id=pk)
            except ClassModel.DoesNotExist:
                return Response({'error': 'Class not found'}, status=404)
            return Response(ClassSerializer(obj).data)

        # Pagination (return payload similar to Students API)
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('row_per_page', request.GET.get('per_page', 50)))
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page)

        serializer = ClassSerializer(page_obj.object_list, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'previous': None if not page_obj.has_previous() else page_obj.previous_page_number(),
            'next': None if not page_obj.has_next() else page_obj.next_page_number(),
        })

    def post(self, request):
        if ClassModel is None:
            return Response({'error': 'ClassModel not available'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = request.data
        serializer = ClassSerializer(data=data)
        if serializer.is_valid():
            obj = ClassModel.objects.create(
                standard=serializer.validated_data.get('standard'),
                section=serializer.validated_data.get('section'),
                academic_year=serializer.validated_data.get('academic_year', '2024-25'),
                is_active=serializer.validated_data.get('is_active', True)
            )
            return Response(ClassSerializer(obj).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        if not pk:
            return Response({'error': 'pk required'}, status=400)
        try:
            obj = ClassModel.objects.get(id=pk)
        except ClassModel.DoesNotExist:
            return Response({'error': 'Class not found'}, status=404)

        serializer = ClassSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            for k, v in serializer.validated_data.items():
                setattr(obj, k, v)
            obj.save()
            return Response(ClassSerializer(obj).data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk=None):
        if not pk:
            return Response({'error': 'pk required'}, status=400)
        try:
            obj = ClassModel.objects.get(id=pk)
        except ClassModel.DoesNotExist:
            return Response({'error': 'Class not found'}, status=404)
        obj.is_active = False
        obj.save()
        return Response({'message': 'Class deactivated'})
