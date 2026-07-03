from django.urls import path,include

from user_management.Views.SignUpView import *
from user_management.Views.SignInView import *
from user_management.Views.ProfileView import *
from user_management.Views.StudentView import *
from user_management.Views.StudentQRCodeView import StudentAddNumberAPIView, StudentVerifyQRAPIView


urlpatterns = [
    
    path('signup/',SignUpView.as_view(),name='signup'),
    path('signin/',SignInView.as_view(),name='signin'),
    path('profile/',ProfileView.as_view(),name='profile'),
    path('profile/<int:id>/',ProfileView.as_view(),name='profile'),
    path('student/',StudentView.as_view(),name='student'),
    path('student/<int:id>/',StudentView.as_view(),name='student'),
    path('student/device/register/', StudentAddNumberAPIView.as_view(), name='student-add-number'),
    path('student/verify-qr/', StudentVerifyQRAPIView.as_view(), name='student-verify-qr'),
    path('qr-login/', QRLoginAPIView.as_view(), name='parent-qr-login'),
]