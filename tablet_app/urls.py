from django.urls import path,include
from tablet_app.Views.pdfGroupView import pdfGroupAPI
from tablet_app.Views.pdfLibraryView import pdfLibraryAPI, StudentpdfListAPI
from tablet_app.Views.TestView import TestAPI
from tablet_app.Views.QuestionsView import QuestionsAPI
from tablet_app.Views.QuestionOptionsView import QuestionOptionsAPI
from tablet_app.Views.StudentTestAttemptView import StudentTestAttemptAPI
from tablet_app.Views.StudentAnswerView import StudentAnswerAPI
from tablet_app.Views.StudentTestFinishView import StudentTestFinishAPI
from tablet_app.Views.StudySessionView import StudySessionAPI

urlpatterns = [

    path('pdf-group/', pdfGroupAPI.as_view(), name='list-pdf-group'),
    path('pdf-group/<int:pk>/', pdfGroupAPI.as_view(), name='retrieve-pdf-group'),
   
    path('pdf-library/', pdfLibraryAPI.as_view(), name='pdf-library'),
    path('pdf-library/<int:pk>/', pdfLibraryAPI.as_view(), name='pdf-library'),
   
    path('test/', TestAPI.as_view(), name='test'),
    path('test/<int:pk>/', TestAPI.as_view(), name='test'),

    path('questions-api/', QuestionsAPI.as_view(), name='questions'),
    path('questions-api/<int:pk>/', QuestionsAPI.as_view(), name='questions'),
    path('pdf-library/', pdfLibraryAPI.as_view(), name='list-pdf-library'),
    path('pdf-library/<int:pk>/', pdfLibraryAPI.as_view(), name='list-pdf-library'),
    path('pdf-library/create/', pdfLibraryAPI.as_view(), name='create-pdf-library'),
    path('pdf-library/update/<int:pk>/', pdfLibraryAPI.as_view(), name='update-pdf-library'),
    path('pdf-library/delete/<int:pk>/', pdfLibraryAPI.as_view(), name='delete-pdf-library'),
    path('student-pdf/<int:student_id>/', StudentpdfListAPI.as_view(), name='student-pdf'),

    path('option/list/', QuestionOptionsAPI.as_view(), name='option'),
    path('option/list/<int:pk>/', QuestionOptionsAPI.as_view(), name='option'),

    path('studenttestattempt/', StudentTestAttemptAPI.as_view(), name='student'),
    path('studenttestattempt/<int:pk>/', StudentTestAttemptAPI.as_view(), name='student'),

    path('studentanswer/', StudentAnswerAPI.as_view(), name='student-answer'),
    path('studentanswer/<int:pk>/', StudentAnswerAPI.as_view(), name='student-answer'),

    path('studenttestattempt/finish/', StudentTestFinishAPI.as_view(),name='finish-test-attempt'),

    path('study-session/', StudySessionAPI.as_view(), name='study-session'),
    path('study-session/<int:pk>/', StudySessionAPI.as_view(), name='study-session-detail'),


]