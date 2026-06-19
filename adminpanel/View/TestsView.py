from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tablet_app.models import TestModel, StudentTestAttemptModel, Subject
from adminpanel.Serializer.TestSerializer import TestSerializer, StudentTestAttemptSerializer
from adminpanel.pagination import ListPagination
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.views import View
from web_project import TemplateLayout, TemplateHelper

class SubjectsAPI(APIView):
    """GET: list all subjects"""
    def get(self, request):
        subjects = Subject.objects.all()
        data = [{'id': s.id, 'name': s.name} for s in subjects]
        return Response({'results': data})

class TestsAPI(APIView):
    """GET: list tests or a single test (by pk)
       POST: create test
    """
    def get(self, request, pk=None):
        if pk:
            test = get_object_or_404(TestModel, pk=pk)
            return Response(TestSerializer(test).data)

        q = request.GET.get('q', '').strip()
        tests_qs = TestModel.objects.all().order_by('-created_at')
        if q:
            tests_qs = tests_qs.filter(Q(title__icontains=q))

        paginator = ListPagination()
        page = paginator.paginate_queryset(tests_qs, request)
        serializer = TestSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TestSerializer(data=request.data)
        if serializer.is_valid():
            test = serializer.save()
            return Response({'data': TestSerializer(test).data, 'message': 'Test created'}, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class StudentTestAttemptAPI(APIView):
    """GET: list test attempts or a single attempt (by pk)
       POST: create test attempt
    """
    def get(self, request, pk=None):
        if pk:
            attempt = get_object_or_404(StudentTestAttemptModel, pk=pk)
            return Response(StudentTestAttemptSerializer(attempt).data)

        student_id = request.GET.get('student_id')
        test_id = request.GET.get('test_id')
        attempts_qs = StudentTestAttemptModel.objects.all().order_by('-started_at')

        if student_id:
            attempts_qs = attempts_qs.filter(student_id=student_id)
        if test_id:
            attempts_qs = attempts_qs.filter(test_id=test_id)

        paginator = ListPagination()
        page = paginator.paginate_queryset(attempts_qs, request)
        serializer = StudentTestAttemptSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = StudentTestAttemptSerializer(data=request.data)
        if serializer.is_valid():
            attempt = serializer.save()
            return Response({'data': StudentTestAttemptSerializer(attempt).data, 'message': 'Test attempt created'}, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class TestDetailView(View):
    """View for displaying test details"""
    template_name = "test_detail.html"

    def get(self, request, pk=None):
        context = TemplateLayout.init(self, {})
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })
        return render(request, self.template_name, context)


