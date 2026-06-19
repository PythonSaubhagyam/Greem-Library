from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from adminpanel.pagination import ListPagination
from adminpanel.Serializer.AnalyticsSerializer import (
    TeacherAnalyticsSerializer,
    CoordinatorAnalyticsSerializer,
    SubjectAnalyticsSerializer,
    TestAnalyticsSerializer,
    HomeworkAnalyticsSerializer
)

class TeachersAnalyticsAPI(APIView):
    """Teacher analytics dashboard"""
    def get(self, request):
        # Get filters
        academic_year = request.GET.get('academic_year')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        class_filter = request.GET.get('class')
        subject_filter = request.GET.get('subject')
        coordinator_filter = request.GET.get('coordinator')
        risk_level = request.GET.get('risk_level')
        search = request.GET.get('search', '').strip()

        # Mock data structure - replace with actual queries
        teachers_data = []

        if search or class_filter or subject_filter:
            # Build mock teacher analytics
            teachers_data = [
                {
                    'teacher_id': 1,
                    'teacher_name': 'John Smith',
                    'subject': 'Mathematics',
                    'classes_assigned': 5,
                    'classes_taken': 85,
                    'tests_conducted': 12,
                    'homework_given': 45,
                    'homework_checked': 42,
                    'avg_student_score': 78.5,
                    'weak_students_count': 8,
                    'last_active_date': timezone.now(),
                    'accountability_score': 85.0,
                },
                {
                    'teacher_id': 2,
                    'teacher_name': 'Sarah Johnson',
                    'subject': 'English',
                    'classes_assigned': 4,
                    'classes_taken': 72,
                    'tests_conducted': 10,
                    'homework_given': 38,
                    'homework_checked': 35,
                    'avg_student_score': 82.3,
                    'weak_students_count': 5,
                    'last_active_date': timezone.now() - timedelta(days=2),
                    'accountability_score': 88.0,
                }
            ]

        paginator = ListPagination()
        page = paginator.paginate_queryset(teachers_data, request)
        serializer = TeacherAnalyticsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class CoordinatorsAnalyticsAPI(APIView):
    """Coordinator analytics dashboard"""
    def get(self, request):
        coordinators_data = [
            {
                'coordinator_id': 1,
                'coordinator_name': 'Principal Admin',
                'classes_handled': 12,
                'teachers_under': 8,
                'students_under': 240,
                'weak_students_count': 35,
                'avg_score': 76.5,
                'teacher_activity_score': 82.0,
                'pending_actions': 5,
                'status': 'Good',
                'control_score': 85.0,
                'has_neglect_alert': False,
            }
        ]

        paginator = ListPagination()
        page = paginator.paginate_queryset(coordinators_data, request)
        serializer = CoordinatorAnalyticsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class SubjectsAnalyticsAPI(APIView):
    """Subject analytics dashboard"""
    def get(self, request):
        subjects_data = [
            {
                'subject_id': 1,
                'subject_name': 'Mathematics',
                'avg_score': 78.5,
                'weak_students_count': 12,
                'best_class': 'Class X-A',
                'weakest_class': 'Class X-B',
                'responsible_teachers': ['John Smith', 'Robert Brown'],
            },
            {
                'subject_id': 2,
                'subject_name': 'English',
                'avg_score': 82.3,
                'weak_students_count': 8,
                'best_class': 'Class X-A',
                'weakest_class': 'Class X-C',
                'responsible_teachers': ['Sarah Johnson'],
            }
        ]

        paginator = ListPagination()
        page = paginator.paginate_queryset(subjects_data, request)
        serializer = SubjectAnalyticsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class TestsAnalyticsAPI(APIView):
    """Tests analytics dashboard"""
    def get(self, request):
        tests_data = [
            {
                'test_id': 1,
                'teacher_name': 'John Smith',
                'subject': 'Mathematics',
                'class_name': 'Class X-A',
                'date': timezone.now() - timedelta(days=5),
                'avg_marks': 75.5,
                'highest_marks': 95.0,
                'lowest_marks': 45.0,
                'students_absent': 2,
                'students_failed': 5,
                'students_passed': 35,
                'retest_needed': True,
            },
            {
                'test_id': 2,
                'teacher_name': 'Sarah Johnson',
                'subject': 'English',
                'class_name': 'Class X-B',
                'date': timezone.now() - timedelta(days=3),
                'avg_marks': 81.0,
                'highest_marks': 98.0,
                'lowest_marks': 52.0,
                'students_absent': 1,
                'students_failed': 2,
                'students_passed': 38,
                'retest_needed': False,
            }
        ]

        paginator = ListPagination()
        page = paginator.paginate_queryset(tests_data, request)
        serializer = TestAnalyticsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class HomeworkAnalyticsAPI(APIView):
    """Homework analytics dashboard"""
    def get(self, request):
        homework_data = [
            {
                'homework_id': 1,
                'teacher_name': 'John Smith',
                'subject': 'Mathematics',
                'class_name': 'Class X-A',
                'assigned_count': 42,
                'submitted_count': 40,
                'pending_count': 2,
                'late_count': 5,
                'checked_count': 38,
                'feedback_given': True,
                'status': 'Good',
            },
            {
                'homework_id': 2,
                'teacher_name': 'Sarah Johnson',
                'subject': 'English',
                'class_name': 'Class X-B',
                'assigned_count': 38,
                'submitted_count': 32,
                'pending_count': 6,
                'late_count': 8,
                'checked_count': 30,
                'feedback_given': True,
                'status': 'Average',
            }
        ]

        paginator = ListPagination()
        page = paginator.paginate_queryset(homework_data, request)
        serializer = HomeworkAnalyticsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
