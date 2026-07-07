from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.db.models import Count

from adminpanel.Serializer.ClassSerializer import ClassSerializer

try:
    from user_management.models import ClassModel, StudentModel, TeacherAssignmentModel
except Exception:
    ClassModel = None
    StudentModel = None
    TeacherAssignmentModel = None


def _get_principal_id(request):
    """
    Resolve the principal (Customer) from request.
    Accepts explicit ?principal_id= param OR uses logged-in user if role=Customer.
    """
    principal_id = request.GET.get('principal_id') or request.data.get('principal_id')
    if principal_id:
        return int(principal_id)
    if (
        request.user.is_authenticated and
        request.user.role and
        request.user.role.type == 'Customer'
    ):
        return request.user.id
    return None


def _scope_classes_to_principal(principal_id):
    """
    Returns a ClassModel queryset scoped to the given principal's school.

    Scoping strategy (three paths, first non-empty wins):
    1. Classes that have students whose parent is this principal.
    2. Classes assigned to teachers under this principal via TeacherAssignmentModel.
    3. No scope — return empty queryset (don't leak other schools' data).
    """
    if not principal_id:
        return ClassModel.objects.none()

    # Path 1: classes via students linked to this principal
    class_ids_via_students = list(
        StudentModel.objects.filter(
            parent__id=principal_id,
            parent__role__type='Customer'
        ).values_list('student_class_id', flat=True).distinct()
    )

    owner_classes = ClassModel.objects.filter(
        school_principal_id=principal_id,
        is_active=True
    )

    if class_ids_via_students:
        student_classes = ClassModel.objects.filter(
            id__in=class_ids_via_students,
            is_active=True
        )
    else:
        student_classes = ClassModel.objects.none()

    # Path 2: classes via TeacherAssignmentModel.school_principal
    class_ids_via_teachers = list(
        TeacherAssignmentModel.objects.filter(
            school_principal_id=principal_id
        ).values_list('assigned_classes__id', flat=True).distinct()
    )

    if class_ids_via_teachers:
        teacher_classes = ClassModel.objects.filter(
            id__in=class_ids_via_teachers,
            is_active=True
        )
    else:
        teacher_classes = ClassModel.objects.none()

    return (student_classes | teacher_classes | owner_classes).distinct()


class ClassAPIView(APIView):

    def get(self, request, pk=None):
        if ClassModel is None:
            return Response({'error': 'ClassModel not available'}, status=500)

        principal_id = _get_principal_id(request)

        # ── Scoped queryset (school-specific + active only) ──
        if principal_id:
            qs = _scope_classes_to_principal(principal_id).order_by('-created_at')
        else:
            # Admin fallback — all active classes
            qs = ClassModel.objects.filter(is_active=True).order_by('-created_at')

        # Optional filters
        standard = request.GET.get('standard')
        academic_year = request.GET.get('academic_year')
        q = request.GET.get('q', '').strip()

        if standard and str(standard).isdigit():
            qs = qs.filter(standard=int(standard))
        if academic_year:
            qs = qs.filter(academic_year__iexact=academic_year)
        if q:
            qs = qs.filter(classname__icontains=q) | qs.filter(section__icontains=q)

        if pk:
            try:
                obj = qs.get(id=pk)
            except ClassModel.DoesNotExist:
                return Response({'error': 'Class not found'}, status=404)
            return Response(ClassSerializer(obj).data)

        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('row_per_page', request.GET.get('per_page', 50)))
        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page)

        # Enrich with student_count
        results = []
        for cls in page_obj.object_list:
            data = ClassSerializer(cls).data
            data['student_count'] = StudentModel.objects.filter(
                student_class=cls
            ).count() if StudentModel else 0
            results.append(data)

        return Response({
            'results':      results,
            'count':        paginator.count,
            'current_page': page_obj.number,
            'total_pages':  paginator.num_pages,
            'previous':     None if not page_obj.has_previous() else page_obj.previous_page_number(),
            'next':         None if not page_obj.has_next() else page_obj.next_page_number(),
        })

    def post(self, request):
        if ClassModel is None:
            return Response({'error': 'ClassModel not available'}, status=500)

        serializer = ClassSerializer(data=request.data)
        if serializer.is_valid():
            school_principal = None
            if (
                request.user.is_authenticated and
                getattr(request.user, 'role', None) and
                request.user.role.type == 'Customer'
            ):
                school_principal = request.user

            obj = ClassModel.objects.create(
                standard=serializer.validated_data.get('standard'),
                section=serializer.validated_data.get('section'),
                academic_year=serializer.validated_data.get('academic_year', '2024-25'),
                classname=serializer.validated_data.get('classname', ''),
                subject=serializer.validated_data.get('subject', ''),
                is_active=True,
                school_principal=school_principal,
            )
            return Response(ClassSerializer(obj).data, status=201)

        return Response(serializer.errors, status=400)

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
        return Response({'message': 'Class deactivated successfully'}, status=200)