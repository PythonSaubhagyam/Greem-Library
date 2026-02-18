from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from rest_framework.permissions import IsAuthenticated
from ..pagination import ListPagination
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from adminpanel.Serializer.StudentDetailSerializer import *
from adminpanel.Serializer.StudentSerializer import *
from django.utils import timezone
from datetime import timedelta,datetime
from django.shortcuts import get_object_or_404
from django.db.models import Avg

class StudentsAPIView(APIView):
    # permission_classes = [IsAuthenticated]
 
    def get(self, request):
        teacher_id = request.query_params.get('teacher_id')
        parent_id = request.query_params.get('parent_id')
        linked_user = request.GET.get("linked_user")
   

        student_id = request.GET.get('id')
        q = request.GET.get('q')
        students = StudentModel.objects.all().order_by('-id')
        
        if student_id:
            # print(student_id,'student_id')
            students = students.filter(id=student_id)

        
        if linked_user:
            students = students.filter(parent__id=linked_user)
        
            print(student_id)

        if parent_id:
            students = students.filter(parent__id=parent_id)
            print(parent_id)
 
        elif teacher_id:
            students = students.filter(parent__id=teacher_id)
 

        if q:
            students = students.filter(
                Q(student_name__icontains=q) |
                Q(device_id__imei_number__icontains=q) |
                Q(parent__last_name__icontains=q) |
                Q(parent__first_name__icontains=q) |
                Q(email__icontains=q) |
                Q(student_class__icontains=q)
            ).distinct()
        
        paginator = ListPagination()
        paginated_students = paginator.paginate_queryset(students,request)
        serializer = StudentsSerializer(paginated_students, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        serializer = StudentsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'data':serializer.data,'message':'Student successfully created'}, status=status.HTTP_201_CREATED)
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self,request,id):
        try:
            student = StudentModel.objects.get(id=id)
        except StudentModel.DoesNotExist:
            return Response({'errors':'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StudentsSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data':serializer.data,'message':'Student successfully updated'}, status=status.HTTP_200_OK)
        return Response({'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,id):
        try:
            student = StudentModel.objects.get(id=id)
        except StudentModel.DoesNotExist:
            return Response({'errors':'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        student.delete()
        return Response({'message':'Student successfully deleted'}, status=status.HTTP_200_OK)

class StudentImportAPI(APIView):

    @transaction.atomic
    def post(self, request):

        file = request.FILES.get("file")
        parent_ids = request.data.getlist("parent")

        if not parent_ids:
            return Response(
                {"error": "Customer is required"},
                status=400
            )

        if not file:
            return Response(
                {"error": "File is required"},
                status=400
            )

        if not file.name.endswith((".csv", ".xlsx")):
            return Response(
                {"error": "Invalid file format"},
                status=400
            )

        # ----- READ FILE -----
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        created = 0
        failed = []

        for index, row in df.iterrows():

            payload = {
                "imei_number": row.get("imei_number"),
                "student_name": row.get("student_name"),
                "email": row.get("email"),
                "student_class": row.get("student_class"),
                "parent": parent_ids,
            }

            serializer = StudentsSerializer(
                data=payload,
                context={"request": request}
            )

            if serializer.is_valid():
                student = serializer.save()

                # manually assign parent
                student.parent.set(
                    UserModel.objects.filter(id__in=parent_ids)
                )

                created += 1
            else:
                failed.append({
                    "row": index + 2,
                    "errors": serializer.errors
                })

        return Response({
            "status": True,
            "created": created,
            "failed": len(failed),
            "errors": failed
        })
    
class pdfLibraryAPI(APIView):
    pagination_classes = ListPagination

    def get(self, request, pk=None):
        q = request.GET.get('q')
        if pk:
            try:
                queryset = pdfLibraryModel.objects.filter(student_id=pk)
                if q:
                    queryset = queryset.filter(Q(title__icontains=q) |
                                               Q(group__name__icontains=q)
                    ).distinct()
                paginator = self.pagination_classes()
                paginated_queryset = paginator.paginate_queryset(queryset, request)
                serializer = pdfSerializer(paginated_queryset,many=True)
                return paginator.get_paginated_response(serializer.data)
            except pdfLibraryModel.DoesNotExist:
                return Response({'status':False,'message':'Pdf not exist'})
            

class pdfGroupAPI(APIView):
    pagination_classes = ListPagination

    def get(self,request,pk=None):
        q = request.GET.get('q')
        if pk:
            groups = pdfGroupModel.objects.filter(pdflibrarymodel__student_id=pk).distinct()
            if q:
                groups = groups.filter(name__icontains=q)
            paginator = self.pagination_classes()
            paginated_groups = paginator.paginate_queryset(groups,request)
            serializer = pdfGroupSerializer(paginated_groups,many=True,context={'student_id':pk})
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response({'status':False,'message':'Student id is required'},status=status.HTTP_400_BAD_REQUEST)


class StudentsTestResultView(APIView):
    pagination_classes = ListPagination

    def get(self,request,pk=None):
        q = request.GET.get('q')
        if pk:
            try:
               student_result = StudentTestAttemptModel.objects.filter(student_id=pk)
               if q:
                   student_result = student_result.filter(
                       Q(test__title__icontains=q) |
                       Q(score__icontains=q) |
                       Q(test__question_type__icontains=q) |
                       Q(test__total_marks__icontains=q) |
                       Q(test__duration_minutes__icontains=q) |
                       Q(test__number_of_questions__icontains=q) |
                       Q(started_at__icontains=q) |
                       Q(completed_at__icontains=q)
                     ).distinct()
               paginator = self.pagination_classes()
               paginated_result_details = paginator.paginate_queryset(student_result,request)
               serializer = StudentTestAttemptSerializer(paginated_result_details,many=True)
               return paginator.get_paginated_response(serializer.data)
            except StudentTestAttemptModel.DoesNotExist:
                return Response({'status':False,'message':'Test information not available for this student'})
            

class StudentSummaryAPIView(APIView):

    def get(self, request, student_id):

        student = get_object_or_404(StudentModel, id=student_id)

        # ------------------------
        # PDFs count
        # ------------------------
        pdf_count = pdfLibraryModel.objects.filter(
            student=student
        ).count()

        # ------------------------
        # Groups count
        # ------------------------
        group_count = pdfGroupModel.objects.filter(
            pdflibrarymodel__student=student
        ).distinct().count()

        # ------------------------
        # Tests attempted
        # ------------------------
        tests_attempted = StudentTestAttemptModel.objects.filter(
            student=student  # ⚠ adjust if different
        ).count()


        attempts = StudentTestAttemptModel.objects.filter(student=student)

        completed = attempts.filter(is_completes=True).count()
        incomplete = attempts.filter(is_completes=False).count()


        return Response({
            "status": True,
            "counts": {
                "pdfs": pdf_count,
                "groups": group_count,
                "tests_attempted": tests_attempted,
                "completed_tests": completed,
                "incomplete_tests": incomplete,
            },
        }, status=status.HTTP_200_OK)

