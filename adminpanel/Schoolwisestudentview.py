from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from .pagination import ListPagination
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from adminpanel.Serializer.StudentDetailSerializer import *
from adminpanel.Serializer.StudentSerializer import *
from django.utils import timezone
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404
from django.db.models import Avg


class SchoolStudentsAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication] 
    permission_classes = [IsAuthenticated]   # ✅ UNCOMMENT THIS — required for customer filtering

    def get(self, request):
        teacher_id = request.query_params.get('teacher_id')
        parent_id = request.query_params.get('parent_id')
        linked_user = request.GET.get("linked_user")

        def to_int(val):
            try:
                return int(val) if val is not None and str(val) != '' else None
            except (ValueError, TypeError):
                return None

        student_id = request.GET.get('id')
        q = request.GET.get('q')

        # ── 1. Detect customer role FIRST ──────────────────────────────────────
        req_user = request.user
        role_obj = getattr(req_user, 'role', None)
        role_type = None
        if role_obj:
            role_type = getattr(role_obj, 'type', None) or getattr(role_obj, 'name', None)

        is_customer = role_type and str(role_type).lower() == 'customer'

        # ── 2. Base queryset ───────────────────────────────────────────────────
        students = StudentModel.objects.all().order_by('-id')

        # ── 3. If customer → restrict to their school's students IMMEDIATELY ──
        if is_customer:
            # Try filtering by customer field on StudentModel directly
            # Adjust the field name below to match your actual model:
            #   Option A: student has a direct FK to customer user
            #       students = students.filter(customer__id=req_user.id)
            #   Option B: student's customer_name matches req_user.firm_name
            #       students = students.filter(customer_name__iexact=req_user.firm_name)
            #   Option C: student's parent is linked to this customer
            #       students = students.filter(parent__customer__id=req_user.id)

            # ✅ Using firm_name match (most common pattern based on your serializer output)
            firm = getattr(req_user, 'firm_name', None)
            if firm:
                students = students.filter(customer_name__iexact=firm).distinct()
            else:
                # Fallback: only show students where this customer is the parent
                students = students.filter(parent__id=req_user.id).distinct()

        # ── 4. Apply optional filters (only within the already-restricted QS) ─
        student_id_num = to_int(student_id)
        teacher_id_num = to_int(teacher_id)
        parent_id_num  = to_int(parent_id)
        linked_user_num = to_int(linked_user)

        if student_id_num is not None:
            students = students.filter(id=student_id_num)

        if linked_user_num is not None:
            students = students.filter(parent__id=linked_user_num)

        if parent_id_num is not None:
            students = students.filter(parent__id=parent_id_num)
        elif teacher_id_num is not None:
            students = students.filter(parent__id=teacher_id_num)

        if q:
            students = students.filter(
                Q(student_name__icontains=q) |
                Q(device_id__imei_number__icontains=q) |
                Q(parent__last_name__icontains=q) |
                Q(parent__first_name__icontains=q) |
                Q(email__icontains=q) |
                Q(student_class__icontains=q)
            ).distinct()

        # ── 5. Debug helper ────────────────────────────────────────────────────
        if request.GET.get('debug') == '1':
            return Response({
                'debug_user': {
                    'id': getattr(req_user, 'id', None),
                    'email': getattr(req_user, 'email', None),
                    'role_type': role_type,
                    'firm_name': getattr(req_user, 'firm_name', None),
                    'is_customer': is_customer,
                },
                'students_total': StudentModel.objects.count(),
                'students_after_filter': students.count(),
                'sample_student_ids': list(students.values_list('id', flat=True)[:10]),
            })

        # ── 6. Paginate & return ───────────────────────────────────────────────
        paginator = ListPagination()
        paginated_students = paginator.paginate_queryset(students, request)
        serializer = StudentsSerializer(paginated_students, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = StudentsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Student successfully created'}, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        try:
            student = StudentModel.objects.get(id=id)
        except StudentModel.DoesNotExist:
            return Response({'errors': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StudentsSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Student successfully updated'}, status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            student = StudentModel.objects.get(id=id)
        except StudentModel.DoesNotExist:
            return Response({'errors': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        student.delete()
        return Response({'message': 'Student successfully deleted'}, status=status.HTTP_200_OK)