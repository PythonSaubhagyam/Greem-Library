from django.urls import path,include
from tablet_app.Views.pdfGroupView import pdfGroupAPI
from tablet_app.Views.pdfLibraryView import pdfLibraryAPI
from tablet_app.Views.TestView import TestAPI
from tablet_app.Views.QuestionsView import QuestionsAPI
from tablet_app.Views.QuestionOptionsView import QuestionOptionsAPI
from tablet_app.Views.StudentTestAttemptView import StudentTestAttemptAPI
from tablet_app.Views.StudentAnswerView import StudentAnswerAPI
from tablet_app.Views.StudentTestFinishView import StudentTestFinishAPI

urlpatterns = [

    path('pdf-group/', pdfGroupAPI.as_view(), name='list-pdf-group'),
    path('pdf-group/<int:pk>/', pdfGroupAPI.as_view(), name='retrieve-pdf-group'),
    path('pdf-group/create/', pdfGroupAPI.as_view(), name='create-pdf-group'),
    path('pdf-group/update/<int:pk>/', pdfGroupAPI.as_view(), name='update-pdf-group'),
    path('pdf-group/delete/<int:pk>/', pdfGroupAPI.as_view(), name='delete-pdf-group'),

    path('pdf-library/', pdfLibraryAPI.as_view(), name='list-pdf-library'),
    path('pdf-library/<int:pk>/', pdfLibraryAPI.as_view(), name='list-pdf-library'),
    path('pdf-library/create/', pdfLibraryAPI.as_view(), name='create-pdf-library'),
    path('pdf-library/update/<int:pk>/', pdfLibraryAPI.as_view(), name='update-pdf-library'),
    path('pdf-library/delete/<int:pk>/', pdfLibraryAPI.as_view(), name='delete-pdf-library'),

    path('test/', TestAPI.as_view(), name='test-retrieve'),
    path('test/<int:pk>/', TestAPI.as_view(), name='test-list'),
    path('test/create/', TestAPI.as_view(), name='test-create'),
    path('test/update/<int:pk>/', TestAPI.as_view(), name='update-test'),
    path('test/delete/<int:pk>/', TestAPI.as_view(), name='delete-test'),

    path('question/list/', QuestionsAPI.as_view(), name='list-questions'),
    path('question/list/<int:pk>/', QuestionsAPI.as_view(), name='list-questions'),
    path('question/create/', QuestionsAPI.as_view(), name='create-question'),
    path('question/update/<int:pk>/', QuestionsAPI.as_view(), name='update-question'),
    path('question/delete/<int:pk>/', QuestionsAPI.as_view(), name='delete-question'),

    path('option/list/', QuestionOptionsAPI.as_view(), name='list-option'),
    path('option/list/<int:pk>/', QuestionOptionsAPI.as_view(), name='retrieve-option'),
    path('option/create/', QuestionOptionsAPI.as_view(), name='create-option'),
    path('option/update/<int:pk>/', QuestionOptionsAPI.as_view(), name='update-option'),
    path('option/delete/<int:pk>/', QuestionOptionsAPI.as_view(), name='delete-option'),

    path('studenttestattempt/list/', StudentTestAttemptAPI.as_view(), name='list-student'),
    path('studenttestattempt/list/<int:pk>/', StudentTestAttemptAPI.as_view(), name='retrieve-student'),
    path('studenttestattempt/create/', StudentTestAttemptAPI.as_view(), name='create-student'),
    path('studenttestattempt/update/<int:pk>/', StudentTestAttemptAPI.as_view(), name='update-student'),
    path('studenttestattempt/delete/<int:pk>/', StudentTestAttemptAPI.as_view(), name='delete-student'),

    path('studentanswer/', StudentAnswerAPI.as_view(), name='list-student-answer'),
    path('studentanswer/<int:pk>/', StudentAnswerAPI.as_view(), name='retrieve-student-answer'),
    path('studentanswer/create/', StudentAnswerAPI.as_view(), name='create-student-answer'),
    path('studentanswer/update/<int:pk>/', StudentAnswerAPI.as_view(), name='update-student-answer'),
    path('studentanswer/delete/<int:pk>/', StudentAnswerAPI.as_view(), name='delete-student-answer'),

    path('studenttestattempt/finish/', StudentTestFinishAPI.as_view(),name='finish-test-attempt'),


]