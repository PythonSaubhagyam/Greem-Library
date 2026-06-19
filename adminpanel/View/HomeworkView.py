from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from adminpanel.models import HomeworkModel, HomeworkSubmissionModel
from adminpanel.Serializer.HomeworkSerializer import HomeworkSerializer, HomeworkSubmissionSerializer
from ..pagination import ListPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count

class HomeworkAPI(APIView):
    """GET: list homeworks or a single homework (by id)
       POST: create homework
    """
    def get(self, request, pk=None):
        if pk:
            hw = get_object_or_404(HomeworkModel, pk=pk)
            return Response(HomeworkSerializer(hw).data)

        q = request.GET.get('q','').strip()
        hw_qs = HomeworkModel.objects.all().order_by('-created_at')
        if q:
            hw_qs = hw_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        paginator = ListPagination()
        page = paginator.paginate_queryset(hw_qs, request)
        serializer = HomeworkSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = HomeworkSerializer(data=request.data)
        if serializer.is_valid():
            hw = serializer.save()
            return Response({'data':HomeworkSerializer(hw).data,'message':'Homework created'}, status=status.HTTP_201_CREATED)
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class HomeworkSubmissionAPI(APIView):
    def get(self, request, pk=None):
        # if pk provided, list submissions for a homework
        if pk:
            subs = HomeworkSubmissionModel.objects.filter(homework_id=pk).order_by('-submitted_at')
            paginator = ListPagination()
            page = paginator.paginate_queryset(subs, request)
            serializer = HomeworkSubmissionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # otherwise list submissions across homeworks with optional filters
        homework_id = request.GET.get('homework_id')
        student_id = request.GET.get('student_id')
        is_checked = request.GET.get('is_checked')
        subs = HomeworkSubmissionModel.objects.all().order_by('-submitted_at')
        if homework_id:
            subs = subs.filter(homework_id=homework_id)
        if student_id:
            subs = subs.filter(student_id=student_id)
        if is_checked is not None:
            if is_checked.lower() in ['true','1','yes']:
                subs = subs.filter(is_checked=True)
            else:
                subs = subs.filter(is_checked=False)
        paginator = ListPagination()
        page = paginator.paginate_queryset(subs, request)
        serializer = HomeworkSubmissionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = HomeworkSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            sub = serializer.save()
            return Response({'data':HomeworkSubmissionSerializer(sub).data,'message':'Submission created'}, status=status.HTTP_201_CREATED)
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class HomeworkDashboardAPI(APIView):
    """Return counts: Assigned, Submitted, Pending, Checked for dashboard widgets"""
    def get(self, request):
        total_assigned = HomeworkModel.objects.count()
        total_submitted = HomeworkSubmissionModel.objects.count()
        total_checked = HomeworkSubmissionModel.objects.filter(is_checked=True).count()
        # Pending = assigned but no submission by students; approximate as assigned * students - submitted
        # Simpler: count homeworks that have zero submissions
        assigned_no_submissions = HomeworkModel.objects.annotate(sub_count=Count('submissions')).filter(sub_count=0).count()
        return Response({
            'assigned': total_assigned,
            'submitted': total_submitted,
            'pending': assigned_no_submissions,
            'checked': total_checked,
        })
