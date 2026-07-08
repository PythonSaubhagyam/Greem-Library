from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from ..pagination import ListPagination
from adminpanel.Serializer.StudentDetailSerializer import *
from adminpanel.Serializer.StudentSerializer import *
from rest_framework.permissions import AllowAny

class MobileStudentsAPIView(APIView):
 
    def get(self, request):
        imei_number = request.GET.get('imei_number')
        q = request.GET.get('q')
        students = StudentModel.objects.all().order_by('-id')
        

        if imei_number:
            # print(imei_number,'imei_number')
            students = students.filter(device_id__imei_number=imei_number)
        
        if q:
            print(q,'q')
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

    
    def patch(self, request):
        imei_number = request.query_params.get('imei_number')
        if not imei_number:
            return Response({'errors': 'IMEI number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = StudentModel.objects.get(device_id__imei_number=imei_number)
        except StudentModel.DoesNotExist:
            return Response({'errors': f'Student with IMEI {imei_number} not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        new_imei = data.get('imei_number')
        if new_imei:
            try:
                device = DeviceModel.objects.get(imei_number=new_imei)
                data['device_id'] = device.id
            except DeviceModel.DoesNotExist:
                return Response({'errors': f"Device with IMEI {new_imei} does not exist."},
                                status=status.HTTP_400_BAD_REQUEST)

        customer_id = data.get('customer')
        if customer_id:
            data['parent'] = [customer_id]

        serializer = StudentsSerializer(student, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            if customer_id:
                student.parent.set(UserModel.objects.filter(id=customer_id))
            return Response({'data': serializer.data, 'message': 'Student successfully updated'}, status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    

    def delete(self,request,id):
        try:
            student = StudentModel.objects.get(device_id__imei_number=id)
        except StudentModel.DoesNotExist:
            return Response({'errors':'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        
        student.delete()
        return Response({'message':'Student successfully deleted'}, status=status.HTTP_200_OK)



class StudentUploadPDFAPIView(APIView):
    """
    POST /user/student/pdf/upload/

    Multipart form-data payload:
        unique_number : "8789900709872786"   (device IMEI — identifies the student)
        pdf_file      : <file>
        title         : "Chapter 5 Notes"     (optional)
        total_pages   : 12                    (optional, defaults to 0)
        is_custom     : true/false             (optional, defaults to true — student-uploaded)

    No login required — the device's unique_number identifies the student,
    same pattern as StudentAddNumberAPIView.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        unique_number = request.data.get("unique_number")
        pdf_file      = request.FILES.get("pdf_file")

        if not unique_number:
            return Response({
                "success": False,
                "message": "unique_number is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not pdf_file:
            return Response({
                "success": False,
                "message": "pdf_file is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find device by IMEI
        try:
            device = DeviceModel.objects.get(imei_number=unique_number)
        except DeviceModel.DoesNotExist:
            return Response({
                "success": False,
                "message": "Device not found for this unique_number."
            }, status=status.HTTP_404_NOT_FOUND)

        # Find student linked to this device
        student = StudentModel.objects.filter(device_id=device).first()
        if not student:
            return Response({
                "success": False,
                "message": "No student is registered to this device yet."
            }, status=status.HTTP_404_NOT_FOUND)

        title       = request.data.get("title") or pdf_file.name
        total_pages = request.data.get("total_pages") or 0
        is_custom   = str(request.data.get("is_custom", "true")).lower() != "false"

        try:
            total_pages = int(total_pages)
        except (TypeError, ValueError):
            total_pages = 0

        pdf_obj = pdfLibraryModel.objects.create(
            title=title,
            pdf_file=pdf_file,
            total_pages=total_pages,
            student=student,
            is_custom=is_custom,
        )

        return Response({
            "success": True,
            "message": "PDF uploaded successfully.",
            "data": {
                "id":          pdf_obj.id,
                "title":       pdf_obj.title,
                "pdf_url":     pdf_obj.pdf_file.url if pdf_obj.pdf_file else None,
                "total_pages": pdf_obj.total_pages,
                "student_id":  student.id,
                "student_name": student.student_name,
            }
        }, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        """
        GET /user/student/pdf/upload/?unique_number=8789900709872786

        Returns the list of PDFs uploaded/available for the student
        linked to this device.
        """
        unique_number = request.query_params.get("unique_number")

        if not unique_number:
            return Response({
                "success": False,
                "message": "unique_number is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = DeviceModel.objects.get(imei_number=unique_number)
        except DeviceModel.DoesNotExist:
            return Response({
                "success": False,
                "message": "Device not found for this unique_number."
            }, status=status.HTTP_404_NOT_FOUND)

        student = StudentModel.objects.filter(device_id=device).first()
        if not student:
            return Response({
                "success": False,
                "message": "No student is registered to this device yet."
            }, status=status.HTTP_404_NOT_FOUND)

        pdfs = pdfLibraryModel.objects.filter(
            student=student
        ).order_by('-created_at')

        data = [
            {
                "id":           pdf.id,
                "title":        pdf.title,
                "pdf_url":      pdf.pdf_file.url if pdf.pdf_file else None,
                "total_pages":  pdf.total_pages,
                "is_custom":    pdf.is_custom,
                "is_favorite":  pdf.is_favorite,
                "created_at":   pdf.created_at,
            }
            for pdf in pdfs
        ]

        return Response({
            "success": True,
            "student_id":   student.id,
            "student_name": student.student_name,
            "count":        len(data),
            "data":         data
        }, status=status.HTTP_200_OK)

