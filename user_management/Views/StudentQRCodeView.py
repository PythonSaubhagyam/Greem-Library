from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from ..models import StudentModel, DeviceModel, DeviceQRCodeModel, UserModel
from uuid import uuid4

class StudentAddNumberAPIView(APIView):
    # Support both session authentication and token authentication (e.g. for Flutter mobile app)
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        POST /user/student/device/register/

        Payload:
        {
            "unique_number": "8789978"
        }
        """

        unique_number = request.data.get("unique_number")

        if not unique_number:
            return Response({
                "success": False,
                "message": "unique_number is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create device if it doesn't exist
        device, created = DeviceModel.objects.get_or_create(
            imei_number=unique_number,
            defaults={
                "is_active": True,
                "device_status": "Active"
            }
        )

        # Delete previous unused QR codes
        DeviceQRCodeModel.objects.filter(
            device=device,
            is_used=False
        ).delete()

        # Generate new QR token
        qr_token = f"qr_{uuid4().hex}"

        DeviceQRCodeModel.objects.create(
            device=device,
            qr_data=qr_token,
            is_used=False
        )

        return Response({
            "success": True,
            "isUsed": False,
            "unique_number": unique_number,
            "qrData": qr_token
        }, status=status.HTTP_200_OK)

    def get(self, request):
        """
        GET student/addnumber/ (Check QR Status)
        Returns QR data if unused, otherwise tells the app that the QR has been scanned.
        """
        # Find student profile
        student = StudentModel.objects.filter(email=request.user.email).first()
        if not student:
            student = StudentModel.objects.filter(parent=request.user).first()

        if not student or not student.device_id:
            return Response({
                "success": False,
                "message": "Device not registered for this student."
            }, status=status.HTTP_404_NOT_FOUND)

        device = student.device_id

        qr_obj = DeviceQRCodeModel.objects.filter(device=device).order_by('-created_at').first()

        if not qr_obj:
            # Generate a new QR code if none exists yet
            qr_token = f"qr_{uuid4().hex}"
            qr_obj = DeviceQRCodeModel.objects.create(
                device=device,
                qr_data=qr_token,
                is_used=False
            )

        if qr_obj.is_used:
            return Response({
                "success": True,
                "isUsed": True,
                "message": "QR has already been scanned."
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": True,
                "isUsed": False,
                "qrData": qr_obj.qr_data
            }, status=status.HTTP_200_OK)


class StudentVerifyQRAPIView(APIView):
    """
    POST student/verify-qr/
    Body: { "qr_data": "qr_token_here" }
    Scanner (e.g. Parent/Teacher app) sends the scanned QR data here.
    Verifies and updates status to Used.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        qr_data = request.data.get('qr_data')
        if not qr_data:
            return Response({
                "success": False,
                "message": "qr_data is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            qr_obj = DeviceQRCodeModel.objects.get(qr_data=qr_data)
            if qr_obj.is_used:
                return Response({
                    "success": False,
                    "message": "QR has already been scanned/used."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update status to Used
            qr_obj.is_used = True
            qr_obj.save()

            return Response({
                "success": True,
                "message": "QR code verified and status updated to Used."
            }, status=status.HTTP_200_OK)

        except DeviceQRCodeModel.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid QR code."
            }, status=status.HTTP_404_NOT_FOUND)
