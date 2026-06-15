from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Q
from collections import defaultdict
from tablet_app.models import *
from tablet_app.serializers import StudentGroupSerializer
from user_management.models import *
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, F, FloatField, Count
from django.utils.timezone import localtime
from tablet_app.serializers import *

#  HELPER FUNCTIONS FOR STATUS & LAST ACTIVITY
def get_student_status(student):
    """
    Calculate student status: Active or Inactive
    Active = Has activity in last 7 days
    """
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Check recent study sessions
    recent_study = StudySession.objects.filter(
        student=student,
        start_time__gte=seven_days_ago
    ).exists()
    
    # Check recent test attempts
    recent_tests = StudentTestAttemptModel.objects.filter(
        student=student,
        started_at__gte=seven_days_ago
    ).exists()
    
    return 'Active' if (recent_study or recent_tests) else 'Inactive'


def get_last_activity(student):
    """
    Get student's last activity date and time
    Checks both study sessions and test attempts
    """
    last_study = StudySession.objects.filter(student=student).order_by('-end_time').first()
    last_test = StudentTestAttemptModel.objects.filter(student=student).order_by('-completed_at').first()
    
    # Determine which is more recent
    last_activity_time = None
    
    if last_study and last_test:
        study_time = last_study.end_time
        test_time = last_test.completed_at
        last_activity_time = max(study_time, test_time) if test_time else study_time
    elif last_study:
        last_activity_time = last_study.end_time
    elif last_test:
        last_activity_time = last_test.completed_at
    
    if last_activity_time:
        return timezone.localtime(last_activity_time).strftime('%Y-%m-%d')
    
    return 'Never'

class TeacherDashboardAPI(APIView):
    """
    Teacher Dashboard - First step when teacher logs in
    
    📊 TEACHER DASHBOARD FLOW (as per teacher.docx):
    Step 1 → Select Class (this API provides class list)
    Step 2 → Select Subject (if multiple) - handled by ClassSelectionAPI
    Step 3 → View Analytics - handled by EnhancedClassOverviewAPI
    
    This API shows:
    - Teacher info with role (Subject Teacher / Class Teacher / Admin)
    - My Batches (for tuition scenario) - prominently displayed
    - My Classes (assigned classes)
    - Quick stats overview
    - Recent activity
    
    Role-based access:
    - Subject Teacher: Only subject analytics
    - Class Teacher: All subject overview for their class
    - Admin/Principal: Whole school analytics
    """

    def get(self, request, teacher_id):
        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        # Get teacher assignment and determine role
        teacher_role = 'subject_teacher'  # Default role
        homeroom_class = None
        
        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = teacher_assignment.assigned_classes.all()
            assigned_subjects = teacher_assignment.assigned_subjects.all()
            teacher_role = teacher_assignment.teacher_role or 'subject_teacher'
            homeroom_class = teacher_assignment.homeroom_class
        except TeacherAssignmentModel.DoesNotExist:
            # Fallback: Teacher has no formal assignment yet
            students = StudentModel.objects.filter(parent__id=teacher_id).distinct()
            assigned_classes = ClassModel.objects.filter(students__in=students).distinct()
            assigned_subjects = Subject.objects.filter(testmodel__created_by=teacher).distinct()

        # 📂 MY BATCHES - For tuition scenario (prominently displayed first)
        try:
            from user_management.models import BatchModel
            batches = BatchModel.objects.filter(teacher=teacher, is_active=True)
            batches_data = []
            for batch in batches:
                batch_students = batch.students.all()
                # Calculate batch average performance
                batch_percentages = []
                for student in batch_students:
                    attempts = StudentTestAttemptModel.objects.filter(student=student)
                    for a in attempts:
                        if a.test.total_marks > 0:
                            batch_percentages.append((a.score / a.test.total_marks) * 100)
                
                batch_avg = round(sum(batch_percentages) / len(batch_percentages), 1) if batch_percentages else 0
                
                batches_data.append({
                    'id': batch.id,
                    'name': batch.name,
                    'timing': batch.timing,
                    'days': batch.days,
                    'student_count': batch_students.count(),
                    'avg_performance': batch_avg,
                    'class_display': batch.class_ref.get_display_name() if batch.class_ref else f"Class {batch.student_class}" if batch.student_class else None,
                    'subject': batch.subject.name if batch.subject else None
                })
        except ImportError:
            batches_data = []

        # 🏫 MY CLASSES - Build classes data with student counts and subjects
        classes_data = []
        for class_obj in assigned_classes:
            class_students = class_obj.students.all()
            
            # Role-based subject access:
            # - Class teacher sees all subjects for their homeroom class
            # - Subject teacher sees only assigned subjects
            if teacher_role == 'class_teacher' and homeroom_class and homeroom_class.id == class_obj.id:
                # Class teacher: show all subjects for this class
                class_subjects = Subject.objects.filter(
                    testmodel__student__student_class=class_obj
                ).distinct()
                print(class_subjects,'class_subjectsclass_subjectsclass_subjects')
            else:
                # Subject teacher: only assigned subjects
                class_subjects = assigned_subjects

            classes_data.append({
                'id': class_obj.id,
                'class_name': class_obj.get_display_name(),
                'standard': class_obj.standard,
                'section': class_obj.section or '',
                'academic_year': class_obj.academic_year,
                'student_count': class_students.count(),
                'subjects': [{'id': s.id, 'name': s.name} for s in class_subjects],
                'is_homeroom': homeroom_class and homeroom_class.id == class_obj.id
            })

        # Recent activity - only show teacher's subject-related activity
        if teacher_role == 'subject_teacher':
            recent_tests = TestModel.objects.filter(
                created_by=teacher,
                subject__in=assigned_subjects
            ).order_by('-created_at')[:5]
        else:
            recent_tests = TestModel.objects.filter(created_by=teacher).order_by('-created_at')[:5]

        # Quick stats - subject-filtered for subject teachers
        if teacher_role == 'subject_teacher':
            total_students = StudentModel.objects.filter(
                student_class__in=assigned_classes
            ).distinct().count()
            total_tests_created = TestModel.objects.filter(
                created_by=teacher,
                subject__in=assigned_subjects
            ).count()
            pending_submissions = StudentTestAttemptModel.objects.filter(
                test__created_by=teacher,
                test__subject__in=assigned_subjects,
                completed_at__isnull=True
            ).count()
        else:
            total_students = StudentModel.objects.filter(student_class__in=assigned_classes).distinct().count()
            total_tests_created = TestModel.objects.filter(created_by=teacher).count()
            pending_submissions = StudentTestAttemptModel.objects.filter(
                test__created_by=teacher,
                completed_at__isnull=True
            ).count()

        return Response({
            'teacher_info': {
                'id': teacher.id,
                'name': f"{teacher.first_name} {teacher.last_name}",
                'email': teacher.email,
                'role': teacher_role,  # 'subject_teacher', 'class_teacher', or 'admin'
                'role_display': {
                    'subject_teacher': 'Subject Teacher',
                    'class_teacher': 'Class Teacher',
                    'admin': 'Admin / Principal'
                }.get(teacher_role, 'Teacher')
            },
            # 📂 My Batches - Tuition scenario (displayed first in sidebar)
            'my_batches': batches_data,
            # 🏫 My Classes
            'my_classes': classes_data,
            # Subject list for filtering
            'my_subjects': [{'id': s.id, 'name': s.name} for s in assigned_subjects],
            # Quick stats
            'quick_stats': {
                'total_students': total_students,
                'total_tests_created': total_tests_created,
                'pending_submissions': pending_submissions,
                'total_batches': len(batches_data)
            },
            # Recent activity
            'recent_activity': [{
                'id': t.id,
                'title': t.title,
                'subject': t.subject.name if t.subject else None,
                'created_at': timezone.localtime(t.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'student_count': t.student.count()
            } for t in recent_tests],
            # Flow guidance - tells frontend what to do next
            'next_step': 'Select a class or batch to view analytics',
            'flow_hint': 'Step 1 of 3: Select Class → Select Subject → View Analytics'
        })


class ClassSelectionAPI(APIView):
    """
    Class Selection System - Step 2 in teacher flow
    
    📊 TEACHER DASHBOARD FLOW (as per teacher.docx):
    Step 1 → Select Class ✓ (from Dashboard)
    Step 2 → Select Subject (THIS API - shows subjects for selected class)
    Step 3 → View Analytics
    
    After user selects a class from Dashboard, this API shows:
    - Class details
    - Available subjects (filtered by teacher assignment)
    - Batches within this class
    - Class-level quick stats
    
    🔐 Subject-Based Access Control:
    - Math teacher sees only Math tests, Math analytics
    - Science teacher sees only Science
    - Class teacher sees all subjects for their class
    """

    def get(self, request, teacher_id):
        class_id = request.GET.get('class_id')  # Selected class from Step 1
        
        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        # Get teacher assignment and role
        teacher_role = 'subject_teacher'
        homeroom_class = None
        
        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = teacher_assignment.assigned_classes.all()
            assigned_subjects = teacher_assignment.assigned_subjects.all()
            teacher_role = teacher_assignment.teacher_role or 'subject_teacher'
            homeroom_class = teacher_assignment.homeroom_class
        except TeacherAssignmentModel.DoesNotExist:
            # Fallback to old approach
            students = StudentModel.objects.filter(parent__id=teacher_id).distinct()
            assigned_classes = ClassModel.objects.filter(students__in=students).distinct()
            assigned_subjects = Subject.objects.filter(testmodel__created_by=teacher).distinct()

        # If specific class is requested, show detailed view for that class
        if class_id:
            try:
                class_obj = ClassModel.objects.get(id=class_id)
                
                # Verify teacher has access to this class
                if class_obj not in assigned_classes:
                    return Response({'error': 'You are not assigned to this class'}, status=403)
                
                class_students = class_obj.students.all()
                
                # 🔐 Subject-Based Access Control
                # Class teacher sees all subjects, Subject teacher sees only their subjects
                if teacher_role == 'class_teacher' and homeroom_class and homeroom_class.id == class_obj.id:
                    # Class teachers get ALL subjects for their homeroom class
                    available_subjects = Subject.objects.filter(is_active=True)
                else:
                    # Subject teachers only see their assigned subjects
                    available_subjects = assigned_subjects
                
                # Get batches for this class
                try:
                    batches = BatchModel.objects.filter(
                        teacher=teacher,
                        class_ref=class_obj,
                        is_active=True
                    )
                    batch_data = [{
                        'id': b.id,
                        'name': b.name,
                        'timing': b.timing,
                        'days': b.days,
                        'student_count': b.students.count(),
                        'subject': b.subject.name if b.subject else None
                    } for b in batches]
                except:
                    batch_data = []
                
                # Class-level quick stats (subject filtered)
                if teacher_role == 'subject_teacher':
                    class_tests = TestModel.objects.filter(
                        student__student_class=class_obj,
                        subject__in=assigned_subjects
                    ).distinct()
                else:
                    class_tests = TestModel.objects.filter(
                        student__student_class=class_obj
                    ).distinct()
                
                return Response({
                    'teacher_id': teacher_id,
                    'teacher_role': teacher_role,
                    'selected_class': {
                        'id': class_obj.id,
                        'class_name': class_obj.get_display_name(),
                        'standard': class_obj.standard,
                        'section': class_obj.section or '',
                        'academic_year': class_obj.academic_year,
                        'student_count': class_students.count(),
                        'is_homeroom': homeroom_class and homeroom_class.id == class_obj.id
                    },
                    # Step 2: Select Subject from this list
                    'available_subjects': [{'id': s.id, 'name': s.name} for s in available_subjects],
                    'batches': batch_data,
                    'class_stats': {
                        'total_tests': class_tests.count(),
                        'total_students': class_students.count()
                    },
                    'next_step': 'Select a subject to view detailed analytics',
                    'flow_hint': 'Step 2 of 3: Class Selected → Select Subject → View Analytics'
                })
            except ClassModel.DoesNotExist:
                return Response({'error': 'Class not found'}, status=404)

        # If no class_id, return all available classes (same as before)
        class_data = []
        for class_obj in assigned_classes:
            class_students = class_obj.students.all()

            # Get batches for this class
            try:
                batches = BatchModel.objects.filter(
                    teacher=teacher,
                    class_ref=class_obj,
                    is_active=True
                )
                batch_data = [{
                    'id': b.id,
                    'name': b.name,
                    'timing': b.timing,
                    'student_count': b.students.count()
                } for b in batches]
            except:
                batch_data = []

            # Subject access based on role
            if teacher_role == 'class_teacher' and homeroom_class and homeroom_class.id == class_obj.id:
                class_subjects = Subject.objects.filter(
                    testmodel__student__student_class=class_obj
                ).distinct()
            else:
                class_subjects = assigned_subjects

            class_data.append({
                'id': class_obj.id,
                'class_name': class_obj.get_display_name(),
                'standard': class_obj.standard,
                'section': class_obj.section or '',
                'student_count': class_students.count(),
                'subjects': [{'id': s.id, 'name': s.name} for s in class_subjects],
                'batches': batch_data,
                'is_homeroom': homeroom_class and homeroom_class.id == class_obj.id
            })

        return Response({
            'teacher_id': teacher_id,
            'teacher_role': teacher_role,
            'available_classes': class_data,
            'flow_hint': 'Step 1 of 3: Select a class to proceed'
        })


class EnhancedClassOverviewAPI(APIView):
    # """
    # Enhanced Class Overview Page - Step 3 in teacher flow (FINAL STEP)
    
    # 📊 TEACHER DASHBOARD FLOW (as per teacher.docx):
    # Step 1 → Select Class ✓
    # Step 2 → Select Subject ✓
    # Step 3 → View Analytics (THIS API)
    
    # 👨‍🏫 HOW TEACHER SEES CLASS PERFORMANCE (from teacher.docx):
    # When Math teacher opens Class 8A, he sees:
    # - Class average (Math only) ✓
    # - Weak math topics ✓
    # - Difficulty analysis (Math only) ✓
    # - Student ranking (Math only) ✓
    # - NOT full academic data
    
    # 🔐 Subject-Based Access Control:
    # - Math teacher sees: ✔ Math tests, ✔ Math homework, ✔ Math analytics, ❌ Cannot see Science
    # - Science teacher sees only science
    # - Class teacher sees all subjects for their homeroom class
    # """

    # def get(self, request, teacher_id):
    #     class_id = request.GET.get('class_id')
    #     subject_id = request.GET.get('subject')
    #     date_range = request.GET.get('date_range', '30')  # days

    #     if not class_id:
    #         return Response({'error': 'class_id parameter is required'}, status=400)

    #     try:
    #         teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
    #     except UserModel.DoesNotExist:
    #         return Response({'error': 'Teacher not found'}, status=404)

    #     # Get the class object
    #     try:
    #         class_obj = ClassModel.objects.get(id=class_id)
    #     except ClassModel.DoesNotExist:
    #         return Response({'error': 'Class not found'}, status=404)

    #     # Get teacher assignment and role
    #     teacher_role = 'subject_teacher'
    #     assigned_subjects = Subject.objects.none()
    #     homeroom_class = None
        
    #     try:
    #         teacher_assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
    #         if class_obj not in teacher_assignment.assigned_classes.all():
    #             return Response({'error': 'You are not assigned to this class'}, status=403)
    #         assigned_subjects = teacher_assignment.assigned_subjects.all()
    #         teacher_role = teacher_assignment.teacher_role or 'subject_teacher'
    #         homeroom_class = teacher_assignment.homeroom_class
    #     except TeacherAssignmentModel.DoesNotExist:
    #         # Fallback: Get subjects from tests created by teacher
    #         assigned_subjects = Subject.objects.filter(testmodel__created_by=teacher).distinct()

    #     # Get students in this class
    #     students = class_obj.students.all()

    #     #Using Lector / Not Using
    #     using_lector = students.filter(device_id__isnull=False).count()
    #     not_using_lector = students.filter(device_id__isnull=True).count()


    #     if not students.exists():
    #         return Response({'error': 'No students found for this class'}, status=404)

    #     # 🔐 SUBJECT-BASED ACCESS CONTROL
    #     # Validate that teacher can access requested subject
    #     if subject_id:
    #         try:
    #             requested_subject = Subject.objects.get(id=subject_id)
    #             # Class teacher can access all subjects for homeroom, subject teacher only assigned subjects
    #             is_class_teacher_for_this_class = (
    #                 teacher_role == 'class_teacher' and 
    #                 homeroom_class and 
    #                 homeroom_class.id == class_obj.id
    #             )
    #             if not is_class_teacher_for_this_class and requested_subject not in assigned_subjects:
    #                 return Response({
    #                     'error': f'You do not have access to {requested_subject.name} analytics. '
    #                              f'You can only view: {", ".join([s.name for s in assigned_subjects])}'
    #                 }, status=403)
    #         except Subject.DoesNotExist:
    #             return Response({'error': 'Subject not found'}, status=404)

    #     # Filter test attempts by subject (Subject-Based Access Control)
    #     test_attempts = StudentTestAttemptModel.objects.filter(student__in=students)
    #     tests = TestModel.objects.filter(student__in=students)

    #     if subject_id:
    #         # Filter by specific subject
    #         test_attempts = test_attempts.filter(test__subject_id=subject_id)
    #         tests = tests.filter(subject_id=subject_id)
    #     else:
    #         # No subject specified - for subject teachers, show only their subjects
    #         # For class teachers, show all subjects
    #         is_class_teacher_for_this_class = (
    #             teacher_role == 'class_teacher' and 
    #             homeroom_class and 
    #             homeroom_class.id == class_obj.id
    #         )
    #         if not is_class_teacher_for_this_class:
    #             test_attempts = test_attempts.filter(test__subject__in=assigned_subjects)
    #             tests = tests.filter(subject__in=assigned_subjects)

    #     # Calculate subject-specific class average
    #     percentages = []
    #     for attempt in test_attempts:
    #         if attempt.test.total_marks > 0:
    #             percentage = (attempt.score / attempt.test.total_marks) * 100
    #             percentages.append(percentage)

    #     class_average = round(sum(percentages) / len(percentages), 2) if percentages else 0

    #     # Engagement Score
    #     seven_days_ago = timezone.now() - timedelta(days=7)

    #     total_sessions = StudySession.objects.filter(
    #         student__in=students,
    #         start_time__gte=seven_days_ago
    #     ).count()

    #     expected_sessions = students.count() * 7
    #     session_score = (total_sessions / expected_sessions * 100) if expected_sessions > 0 else 0

    #     students_gave_test = test_attempts.filter(
    #         started_at__gte=seven_days_ago
    #     ).values('student').distinct().count()
    #     test_score = (students_gave_test / students.count() * 100) if students.count() > 0 else 0

    #     active_students = StudySession.objects.filter(
    #         student__in=students,
    #         start_time__gte=seven_days_ago
    #     ).values('student').distinct().count()
    #     active_score = (active_students / students.count() * 100) if students.count() > 0 else 0

    #     engagement_score = round(
    #         (session_score * 0.4) + (test_score * 0.4) + (active_score * 0.2), 1
    #     )

    #     # Engagement Label
    #     if engagement_score >= 75:
    #         engagement_label = 'High'
    #     elif engagement_score >= 50:
    #         engagement_label = 'Medium'
    #     else:
    #         engagement_label = 'Low'

    #     # Student ranking (subject only - as per doc)
    #     # 🔥 SHOW ALL STUDENTS - even those with no test data
    #     student_rankings = []
    #     for student in students:
    #         student_attempts = test_attempts.filter(student=student)
            
    #         # Calculate score only if student has test attempts
    #         if student_attempts.exists():
    #             student_percentages = []
    #             for attempt in student_attempts:
    #                 if attempt.test.total_marks > 0:
    #                     percentage = (attempt.score / attempt.test.total_marks) * 100
    #                     student_percentages.append(percentage)

    #             if student_percentages:
    #                 avg_percentage = sum(student_percentages) / len(student_percentages)
    #                 student_rankings.append({
    #                     'student_id': student.id,
    #                     'student_name': student.student_name,
    #                     'average_score': round(avg_percentage, 2),
    #                     'average_score_display': f'{round(avg_percentage, 2)} %',
    #                     'test_count': len(student_percentages),
    #                     'status': get_student_status(student),  # ✅ Active/Inactive
    #                     'last_activity': get_last_activity(student),  # ✅ Last activity date
    #                 })
    #         else:
    #             # ✅ SHOW STUDENTS WITH NO TEST DATA - Still show status and activity
    #             student_rankings.append({
    #                 'student_id': student.id,
    #                 'student_name': student.student_name,
    #                 'average_score': 0,
    #                 'average_score_display': 'N/A',
    #                 'test_count': 0,
    #                 'status': get_student_status(student),  # ✅ Active/Inactive
    #                 'last_activity': get_last_activity(student),  # ✅ Last activity date
    #             })

    #     # Sort: First by status (Active first), then by average score (descending)
    #     student_rankings.sort(key=lambda x: (x['status'] == 'Inactive', -x['average_score']))

    #     # Add ranks
    #     for i, student in enumerate(student_rankings):
    #         student['rank'] = i + 1

    #     # Weak topics analysis (as per doc - "Weak math topics")
    #     # weak_topics = []
    #     # if subject_id:
    #     #     questions = QuestionsModel.objects.filter(
    #     #         test__subject_id=subject_id, 
    #     #         test__student__in=students
    #     #     ).distinct()
            
    #     #     for question in questions:
    #     #         answers = StudentAnswerModel.objects.filter(
    #     #             attempt__test__subject_id=subject_id,
    #     #             attempt__student__in=students,
    #     #             question=question
    #     #         )

    #     #         if answers.exists():
    #     #             correct_answers = answers.filter(selected_option__is_correct=True).count()
    #     #             total_answers = answers.count()
    #     #             accuracy = (correct_answers / total_answers) * 100 if total_answers > 0 else 0

    #     #             if accuracy < 70:  # Consider topic weak if accuracy < 70%
    #     #                 weak_topics.append({
    #     #                     'question_text': question.question_text[:100] + "..." if len(question.question_text) > 100 else question.question_text,
    #     #                     'accuracy': round(accuracy, 2),
    #     #                     'total_attempts': total_answers,
    #     #                     'difficulty_level': 'Hard' if accuracy < 50 else 'Medium'
    #     #                 })

    #     # # Difficulty analysis (as per doc - "Difficulty analysis (Math only)")
    #     # difficulty_analysis = {
    #     #     'hard_questions': len([t for t in weak_topics if t['difficulty_level'] == 'Hard']),
    #     #     'medium_questions': len([t for t in weak_topics if t['difficulty_level'] == 'Medium']),
    #     #     'total_weak_areas': len(weak_topics)
    #     # }

    #     # Determine subject name for response
    #     subject_name = 'All Assigned Subjects'
    #     if subject_id:
    #         try:
    #             subject_name = Subject.objects.get(id=subject_id).name
    #         except Subject.DoesNotExist:
    #             subject_name = 'Unknown'

    #     return Response({
    #         'class_id': class_obj.id,
    #         'class_name': class_obj.get_display_name(),
    #         'subject': subject_name,
    #         'teacher_role': teacher_role,
    #         # Class average (subject only) - as per doc
    #         'class_average': class_average,
    #         'total_students': students.count(),
    #         'students_with_data': len(student_rankings),
    #         # Student ranking (subject only) - as per doc
    #         'student_rankings': student_rankings[:10],  # Top 10 students
    #         # Weak topics - as per doc
    #         # 'weak_topics': sorted(weak_topics, key=lambda x: x['accuracy'])[:10],
    #         'weak_topics': [],
    #         # Difficulty analysis (subject only) - as per doc
    #         # 'difficulty_analysis': difficulty_analysis,
    #         'difficulty_analysis': {
    #             'hard_questions': 0,
    #             'medium_questions': 0,
    #             'total_weak_areas': 0
    #         },
    #         'total_tests': tests.count(),
    #         'date_range': f"Last {date_range} days",
    #         # Access info
    #         'access_note': f'Showing {subject_name} analytics only' if subject_id else 'Showing analytics for all your assigned subjects',
    #         'flow_complete': True,
    #         'flow_hint': 'Step 3 of 3: Analytics View - Click on student to see detailed profile',
    #         'lector_usage': {
    #             'using_lector': using_lector,
    #             'not_using_lector': not_using_lector,
    #         },
    #         'engagement': {
    #             'score': engagement_score,
    #             'label': engagement_label,
    #             'active_students': active_students,
    #         },
    #     })
    """
    Enhanced Class Overview — Step 3 in teacher flow.
    FIXED: weak_topics and difficulty_analysis are now computed (not []/0).
    """
 
    def get(self, request, teacher_id):
        class_id   = request.GET.get('class_id')
        subject_id = request.GET.get('subject')
        date_range = request.GET.get('date_range', '30')
 
        if not class_id:
            return Response({'error': 'class_id parameter is required'}, status=400)
 
        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)
 
        try:
            class_obj = ClassModel.objects.get(id=class_id)
        except ClassModel.DoesNotExist:
            return Response({'error': 'Class not found'}, status=404)
 
        teacher_role      = 'subject_teacher'
        assigned_subjects = Subject.objects.none()
        homeroom_class    = None
 
        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(
                teacher=teacher, is_active=True
            )
            if class_obj not in teacher_assignment.assigned_classes.all():
                return Response(
                    {'error': 'You are not assigned to this class'}, status=403
                )
            assigned_subjects = teacher_assignment.assigned_subjects.all()
            teacher_role      = teacher_assignment.teacher_role or 'subject_teacher'
            homeroom_class    = teacher_assignment.homeroom_class
        except TeacherAssignmentModel.DoesNotExist:
            assigned_subjects = Subject.objects.filter(
                testmodel__created_by=teacher
            ).distinct()
 
        students = class_obj.students.all()
        if not students.exists():
            return Response({'error': 'No students found for this class'}, status=404)
 
        using_lector     = students.filter(device_id__isnull=False).count()
        not_using_lector = students.filter(device_id__isnull=True).count()
 
        # Subject access control
        if subject_id:
            try:
                requested_subject = Subject.objects.get(id=subject_id)
                is_class_teacher  = (
                    teacher_role == 'class_teacher' and
                    homeroom_class and
                    homeroom_class.id == class_obj.id
                )
                if not is_class_teacher and requested_subject not in assigned_subjects:
                    return Response({
                        'error': (
                            f'You do not have access to {requested_subject.name} analytics. '
                            f'You can only view: '
                            f'{", ".join(s.name for s in assigned_subjects)}'
                        )
                    }, status=403)
            except Subject.DoesNotExist:
                return Response({'error': 'Subject not found'}, status=404)
 
        test_attempts = StudentTestAttemptModel.objects.filter(student__in=students)
        tests         = TestModel.objects.filter(student__in=students)
 
        is_class_teacher_for_this_class = (
            teacher_role == 'class_teacher' and
            homeroom_class and
            homeroom_class.id == class_obj.id
        )
 
        if subject_id:
            test_attempts = test_attempts.filter(test__subject_id=subject_id)
            tests         = tests.filter(subject_id=subject_id)
        elif not is_class_teacher_for_this_class:
            test_attempts = test_attempts.filter(test__subject__in=assigned_subjects)
            tests         = tests.filter(subject__in=assigned_subjects)
 
        # Class average
        percentages = [
            (a.score / a.test.total_marks) * 100
            for a in test_attempts
            if a.test.total_marks > 0
        ]
        class_average = round(sum(percentages) / len(percentages), 2) if percentages else 0
 
        # Engagement score
        seven_days_ago    = timezone.now() - timedelta(days=7)
        total_sessions    = StudySession.objects.filter(
            student__in=students, start_time__gte=seven_days_ago
        ).count()
        expected_sessions = students.count() * 7
        session_score     = (
            total_sessions / expected_sessions * 100
            if expected_sessions > 0 else 0
        )
        students_gave_test = test_attempts.filter(
            started_at__gte=seven_days_ago
        ).values('student').distinct().count()
        test_score   = (students_gave_test / students.count() * 100) if students.count() > 0 else 0
        active_count = StudySession.objects.filter(
            student__in=students, start_time__gte=seven_days_ago
        ).values('student').distinct().count()
        active_score = (active_count / students.count() * 100) if students.count() > 0 else 0
        engagement_score = round(
            session_score * 0.4 + test_score * 0.4 + active_score * 0.2, 1
        )
        engagement_label = (
            'High' if engagement_score >= 75 else
            'Medium' if engagement_score >= 50 else
            'Low'
        )
 
        # Student rankings
        from tablet_app.views import get_student_status, get_last_activity  # reuse helpers
        student_rankings = []
        for student in students:
            s_attempts  = test_attempts.filter(student=student)
            s_pcts      = [
                (a.score / a.test.total_marks) * 100
                for a in s_attempts if a.test.total_marks > 0
            ]
            avg = round(sum(s_pcts) / len(s_pcts), 2) if s_pcts else 0
            student_rankings.append({
                'student_id':            student.id,
                'student_name':          student.student_name,
                'average_score':         avg,
                'average_score_display': f'{avg} %' if s_pcts else 'N/A',
                'test_count':            len(s_pcts),
                'status':                get_student_status(student),
                'last_activity':         get_last_activity(student),
            })
        student_rankings.sort(
            key=lambda x: (x['status'] == 'Inactive', -x['average_score'])
        )
        for i, s in enumerate(student_rankings):
            s['rank'] = i + 1
 
        # ── WEAK TOPICS (previously commented out) ────────────────────────────
        weak_topics = []
        if subject_id:
            questions = QuestionsModel.objects.filter(
                test__subject_id=subject_id,
                test__student__in=students,
            ).distinct()
 
            for question in questions:
                answers = StudentAnswerModel.objects.filter(
                    attempt__test__subject_id=subject_id,
                    attempt__student__in=students,
                    question=question,
                )
                if answers.exists():
                    correct    = answers.filter(selected_option__is_correct=True).count()
                    total      = answers.count()
                    accuracy   = (correct / total) * 100 if total > 0 else 0
                    if accuracy < 70:
                        q_text = question.question_text or ''
                        weak_topics.append({
                            'question_id':     question.id,
                            'question_text': (
                                q_text[:120] + '...' if len(q_text) > 120 else q_text
                            ),
                            'accuracy':        round(accuracy, 2),
                            'correct_answers': correct,
                            'total_attempts':  total,
                            'difficulty_level': (
                                'Hard'   if accuracy < 40 else
                                'Medium' if accuracy < 70 else
                                'Easy'
                            ),
                        })
            # Sort weakest first
            weak_topics.sort(key=lambda x: x['accuracy'])
            weak_topics = weak_topics[:10]
 
        # ── DIFFICULTY ANALYSIS (previously commented out) ────────────────────
        hard_count   = len([t for t in weak_topics if t['difficulty_level'] == 'Hard'])
        medium_count = len([t for t in weak_topics if t['difficulty_level'] == 'Medium'])
        difficulty_analysis = {
            'hard_questions':   hard_count,
            'medium_questions': medium_count,
            'easy_questions':   len([t for t in weak_topics if t['difficulty_level'] == 'Easy']),
            'total_weak_areas': len(weak_topics),
            'note': (
                'Difficulty based on student accuracy: Hard < 40%, Medium 40–70%, Easy > 70%'
            ),
        }
 
        subject_name = 'All Assigned Subjects'
        if subject_id:
            try:
                subject_name = Subject.objects.get(id=subject_id).name
            except Subject.DoesNotExist:
                subject_name = 'Unknown'
 
        return Response({
            'class_id':       class_obj.id,
            'class_name':     class_obj.get_display_name(),
            'subject':        subject_name,
            'teacher_role':   teacher_role,
            'class_average':  class_average,
            'total_students': students.count(),
            'students_with_data': len(student_rankings),
            'student_rankings':   student_rankings[:10],
            'weak_topics':        weak_topics,          # ← NOW POPULATED
            'difficulty_analysis': difficulty_analysis, # ← NOW POPULATED
            'total_tests':    tests.count(),
            'date_range':     f'Last {date_range} days',
            'access_note': (
                f'Showing {subject_name} analytics only'
                if subject_id else
                'Showing analytics for all your assigned subjects'
            ),
            'flow_complete': True,
            'flow_hint': (
                'Step 3 of 3: Analytics View — Click on student to see detailed profile'
            ),
            'lector_usage': {
                'using_lector':     using_lector,
                'not_using_lector': not_using_lector,
            },
            'engagement': {
                'score':           engagement_score,
                'label':           engagement_label,
                'active_students': active_count,
            },
        })
 

class ClassOverviewAPI(APIView):
    """
    Provides an overview of all students in a teacher's class
    """

    def get(self, request, teacher_id):
        # Get students associated with this teacher
        students = StudentModel.objects.filter(parent__id=teacher_id)

        # Get recent study data for all students
        end = timezone.now()
        start = end - timedelta(days=7)

        student_data = []
        for student in students:
            sessions = StudySession.objects.filter(
                student=student,
                start_time__range=(start, end)
            )

            # Calculate metrics
            total_study_time = sum(session.duration for session in sessions)
            session_count = sessions.count()

            # Get recent test scores
            recent_attempts = StudentTestAttemptModel.objects.filter(
                student=student
            ).order_by('-started_at')[:3]

            test_scores = [{
                'test_title': attempt.test.title,
                'score': attempt.score,
                'total_marks': attempt.test.total_marks,
                'percentage': round((attempt.score / attempt.test.total_marks) * 100, 2) if attempt.test.total_marks > 0 else 0
            } for attempt in recent_attempts]

            student_data.append({
                'student_id': student.id,
                'student_name': student.student_name,
                'total_study_time': round(total_study_time/60,2) if total_study_time > 0 else 0,
                'session_count': session_count,
                'recent_tests': test_scores
            })

        return Response({
            'students': student_data,
            'total_students': len(student_data)
        })


# class TestCreationAPI(APIView):
#     """
#     Allows teachers to create tests for their students
#     """

#     def post(self, request):
#         # Extract test data from request
#         title = request.data.get('title')
#         subject_name = request.data.get('subject')
#         duration = request.data.get('duration')
#         total_marks = request.data.get('total_marks')
#         assigned_students = request.data.get('assigned_students', [])

#         # Get or create subject
#         subject, created = Subject.objects.get_or_create(name__iexact=subject_name)

#         # Create the test
#         test = TestModel.objects.create(
#             title=title,
#             subject=subject,
#             duration_minutes=duration,
#             total_marks=total_marks,
#             created_by=request.user  
#         )

#         # Assign to students
#         students = StudentModel.objects.filter(id__in=assigned_students)
#         test.student.set(students)

#         return Response({
#             'status': 'success',
#             'test_id': test.id,
#             'message': 'Test created successfully'
#         })
class TestCreationAPI(APIView):
    def post(self, request):
        title = request.data.get('title')
        subject_name = request.data.get('subject')
        duration = request.data.get('duration')
        total_marks = request.data.get('total_marks')
        number_of_questions = request.data.get('number_of_questions')  #  Add this
        question_type = request.data.get('question_type', 'MCQ')        #  Add this
        shuffle_questions = request.data.get('shuffle_questions', False) # Add this
        enable_timer = request.data.get('enable_timer', False)           #  Add this
        scheduled_date = request.data.get('scheduled_date', None)        # Add this
        assigned_students = request.data.get('assigned_students', [])

        # Validate required fields
        if not number_of_questions or not total_marks or not title:
            return Response(
                {'status': False, 'message': 'title, total_marks and number_of_questions are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject, created = Subject.objects.get_or_create(
            name__iexact=subject_name,
            defaults={'name': subject_name}
        )

        test = TestModel.objects.create(
            title=title,
            subject=subject,
            duration_minutes=duration,
            total_marks=total_marks,
            number_of_questions=number_of_questions,  #  Add this
            question_type=question_type,               # Add this
            shuffle_questions=shuffle_questions,        # Add this
            enable_timer=enable_timer,                  # Add this
            scheduled_date=scheduled_date,              # Add this
            created_by=request.user
        )

        students = StudentModel.objects.filter(id__in=assigned_students)
        test.student.set(students)

        return Response({
            'status': True,
            'test_id': test.id,
            'message': 'Test created successfully'
        })


class ClassPerformanceAnalyticsAPI(APIView):
    """
    Provides performance analytics for the entire class
    """

    def get(self, request, teacher_id):
        # Get students associated with this teacher
        students = StudentModel.objects.filter(parent__id=teacher_id)

        # Calculate performance data per student
        total_students = students.count()
        student_percentages = []

        # For each student, calculate their average percentage across all tests
        for student in students:
            student_attempts = StudentTestAttemptModel.objects.filter(student=student)
            
            if student_attempts.exists():
                # Calculate percentage for each test attempt
                test_percentages = []
                for attempt in student_attempts:
                    if attempt.test.total_marks > 0:
                        percentage = (attempt.score / attempt.test.total_marks) * 100
                        test_percentages.append(percentage)
                
                # Calculate average percentage for this student
                if test_percentages:
                    student_average = sum(test_percentages) / len(test_percentages)
                    student_percentages.append(student_average)

        # Calculate overall class average from student percentages
        class_average = (
            round(sum(student_percentages) / len(student_percentages), 2)
            if student_percentages else 0
        )

        # Get subject-wise performance (using the same logic but with proper percentages)
        overall_test_attempts = StudentTestAttemptModel.objects.filter(
            student__in=students
        )
        
        subjects_performance = {}
        for attempt in overall_test_attempts:
            subject_name = attempt.test.subject.name if attempt.test.subject else "Unknown"
            if subject_name not in subjects_performance:
                subjects_performance[subject_name] = {'total_score': 0, 'total_possible': 0, 'percentages': []}

            # Store individual percentages for proper averaging
            if attempt.test.total_marks > 0:
                percentage = (attempt.score / attempt.test.total_marks) * 100
                subjects_performance[subject_name]['percentages'].append(percentage)

        # Calculate average percentage for each subject
        for subject, data in subjects_performance.items():
            if data['percentages']:
                data['percentage'] = round(sum(data['percentages']) / len(data['percentages']), 2)
            else:
                data['percentage'] = 0

        return Response({
            'class_average': class_average,
            'total_students': total_students,
            'subjects_performance': subjects_performance,
            'total_tests': TestModel.objects.filter(created_by__id=teacher_id).count()
        })


class SubjectFilteredStudentDetailAPI(APIView):
    """
    Student Profile Page with Subject Filter
    
    👨‍🎓 HOW TEACHER SEES SPECIFIC STUDENT (from teacher.docx):
    Click Student Name → Student Profile Page
    
    📘 Subject Filter (Top Toggle):
    [ Math ] [ Science ] [ English ] [ All Subjects* ]
    - Math teacher default → Math
    - Principal / Admin → All Subjects
    
    So Math teacher sees:
    - Math trend graph
    - Math accuracy
    - Math weak topics
    
    🧠 HOW 5 TEACHERS MANAGE SAME STUDENT:
    Each teacher sees only their subject:
    - Math teacher sees: Math performance only
    - Science teacher sees: Science performance only
    """

    def get(self, request, student_id):
        subject_id = request.GET.get('subject')
        teacher_id = request.GET.get('teacher_id')  # Optional: to enforce subject restrictions
        date_range = request.GET.get('date_range', '30')  # days
        
        try:
            student = StudentModel.objects.get(id=student_id)
        except StudentModel.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)

        # Determine user role and allowed subjects
        user_role = None
        allowed_subjects = None  # None means all subjects
        teacher_name = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_role = request.user.role.type if request.user.role else None
            
            # If teacher, get their assigned subjects for access control
            if user_role == 'Teacher':
                try:
                    teacher_assignment = TeacherAssignmentModel.objects.get(
                        teacher=request.user, 
                        is_active=True
                    )
                    allowed_subjects = teacher_assignment.assigned_subjects.all()
                    teacher_name = f"{request.user.first_name} {request.user.last_name}"
                    
                    # Class teachers can see all subjects for their homeroom class
                    if teacher_assignment.teacher_role == 'class_teacher':
                        if teacher_assignment.homeroom_class and student.student_class == teacher_assignment.homeroom_class:
                            allowed_subjects = None  # Can see all subjects
                except TeacherAssignmentModel.DoesNotExist:
                    pass
        
        # Alternative: use teacher_id query param
        if teacher_id and not allowed_subjects:
            try:
                teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
                try:
                    teacher_assignment = TeacherAssignmentModel.objects.get(
                        teacher=teacher, 
                        is_active=True
                    )
                    allowed_subjects = teacher_assignment.assigned_subjects.all()
                    teacher_name = f"{teacher.first_name} {teacher.last_name}"
                except TeacherAssignmentModel.DoesNotExist:
                    pass
            except UserModel.DoesNotExist:
                pass

        # Get study sessions
        end = timezone.now()
        start = end - timedelta(days=int(date_range))
        
        sessions = StudySession.objects.filter(
            student=student,
            start_time__range=(start, end)
        ).order_by('-start_time')

        # Get test attempts
        test_attempts = StudentTestAttemptModel.objects.filter(
            student=student,
            started_at__range=(start, end)
        ).order_by('-started_at')

        # 🔐 Subject-Based Access Control
        if subject_id:
            # Specific subject requested
            sessions = sessions.filter(subject_id=subject_id)
            test_attempts = test_attempts.filter(test__subject_id=subject_id)
        elif allowed_subjects is not None:
            # Teacher can only see their assigned subjects
            sessions = sessions.filter(subject__in=allowed_subjects)
            test_attempts = test_attempts.filter(test__subject__in=allowed_subjects)

        # Group sessions by subject
        subject_sessions = {}
        for session in sessions:
            subject_name = session.subject.name if session.subject else "Unknown"
            if subject_name not in subject_sessions:
                subject_sessions[subject_name] = []
            subject_sessions[subject_name].append({
                'date': session.start_time.date(),
                'duration': session.duration,
                'interaction_count': session.interaction_count,
                'start_time': session.start_time,
                'end_time': session.end_time
            })

        # Test history with performance trends
        test_data = []
        subject_performance = {}
        
        for attempt in test_attempts:
            subject_name = attempt.test.subject.name if attempt.test.subject else "Unknown"
            percentage = round((attempt.score / attempt.test.total_marks) * 100, 2) if attempt.test.total_marks > 0 else 0
            
            test_data.append({
                'test_id': attempt.test.id,
                'test_title': attempt.test.title,
                'subject': subject_name,
                'score': attempt.score,
                'total_marks': attempt.test.total_marks,
                'percentage': percentage,
                'date': attempt.started_at.date(),
                'completed_at': attempt.completed_at
            })
            
            # Track subject performance for trend analysis
            if subject_name not in subject_performance:
                subject_performance[subject_name] = {'scores': [], 'dates': []}
            subject_performance[subject_name]['scores'].append(percentage)
            subject_performance[subject_name]['dates'].append(attempt.started_at.date())

        # Performance trends by subject
        performance_trends = {}
        for subject_name, data in subject_performance.items():
            if data['scores']:
                performance_trends[subject_name] = {
                    'current_score': data['scores'][-1] if data['scores'] else 0,
                    'previous_score': data['scores'][-2] if len(data['scores']) > 1 else 0,
                    'improvement': round(data['scores'][-1] - data['scores'][-2], 2) if len(data['scores']) > 1 else 0,
                    'average_score': round(sum(data['scores']) / len(data['scores']), 2),
                    'total_tests': len(data['scores'])
                }

        # Overall statistics
        total_study_time = sum(session.duration for session in sessions)
        avg_session_duration = round(total_study_time / sessions.count() if sessions.count() > 0 else 0, 2)

        total_tests = test_attempts.count()
        avg_test_score = round(sum(t['percentage'] for t in test_data) / total_tests, 2) if total_tests > 0 else 0

        if avg_test_score >= 75:
            performance_tag = {'label': 'Strong', 'emoji': '🟢', 'color': 'green'}
        elif avg_test_score >= 50:
            performance_tag = {'label': 'Average', 'emoji': '🟡', 'color': 'yellow'}
        else:
            performance_tag = {'label': 'Weak', 'emoji': '🔴', 'color': 'red'}

        # Check if there's any "Unknown" subject data
        has_unknown_subjects = "Unknown" in subject_sessions or any(t['subject'] == "Unknown" for t in test_data)
        subject_tracking_note = "Note: Some study sessions or tests don't have subject information. These are marked as 'Unknown'." if has_unknown_subjects else None

        # Build available subjects for toggle (filtered by teacher access)
        if allowed_subjects is not None:
            available_subjects = list(allowed_subjects.values('id', 'name'))
        else:
            available_subjects = list(Subject.objects.filter(
                testmodel__student=student
            ).distinct().values('id', 'name'))

        # Determine current subject display
        current_subject_display = 'All Subjects'
        if subject_id:
            try:
                current_subject_display = Subject.objects.get(id=subject_id).name
            except Subject.DoesNotExist:
                pass

        return Response({
            'student_id': student.id,
            'student_name': student.student_name,
            'class': student.student_class.get_display_name() if student.student_class else None,
            'date_range': f"Last {date_range} days",
            
            # 📘 Subject Filter Toggle (as per doc)
            'subject_filter': {
                'current_subject': current_subject_display,
                'current_subject_id': subject_id,
                'available_subjects': available_subjects,
                'access_restricted': allowed_subjects is not None,
                'teacher_name': teacher_name
            },

            'performance_tag': performance_tag,
            
            # Study statistics (subject filtered)
            'study_statistics': {
                'total_study_time': total_study_time,
                'session_count': sessions.count(),
                'avg_session_duration': avg_session_duration,
                'subject_distribution': {k: len(v) for k, v in subject_sessions.items()}
            },
            
            # Test statistics (subject filtered)
            'test_statistics': {
                'total_tests': total_tests,
                'average_score': avg_test_score,
                'subject_performance': performance_trends
            },
            
            # Detailed data
            'study_sessions': subject_sessions,
            'test_history': test_data,
            'performance_trends': performance_trends,  # Trend graph data (as per doc)
            
            # Notes
            'subject_tracking_note': subject_tracking_note,
            'access_note': f'Viewing {current_subject_display} data only' if subject_id or allowed_subjects else 'Viewing all subjects'
        })


class StudentDetailViewAPI(APIView):
    """
    Provides detailed information about a specific student
    """

    def get(self, request, student_id):
        try:
            student = StudentModel.objects.get(id=student_id)
        except StudentModel.DoesNotExist:
            return Response({
                'error': 'Student not found'
            }, status=404)

        # Get study sessions for the past month
        end = timezone.now()
        start = end - timedelta(days=30)

        sessions = StudySession.objects.filter(
            student=student,
            start_time__range=(start, end)
        ).order_by('-start_time')

        # Group sessions by subject
        subject_sessions = {}
        for session in sessions:
            subject_name = session.subject.name if session.subject else "Unknown"
            if subject_name not in subject_sessions:
                subject_sessions[subject_name] = []
            subject_sessions[subject_name].append({
                'date': session.start_time.date(),
                'duration': session.duration,
                'interaction_count': session.interaction_count
            })

        # Get test attempts
        test_attempts = StudentTestAttemptModel.objects.filter(
            student=student
        ).order_by('-started_at')

        test_data = [{
            'test_title': attempt.test.title,
            'subject': attempt.test.subject.name if attempt.test.subject else "Unknown",
            'score': attempt.score,
            'total_marks': attempt.test.total_marks,
            'percentage': round((attempt.score / attempt.test.total_marks) * 100, 2) if attempt.test.total_marks > 0 else 0,
            'date': attempt.started_at.date()
        } for attempt in test_attempts]

        # Check for unknown subjects
        has_unknown_subjects = "Unknown" in subject_sessions or any(t['subject'] == "Unknown" for t in test_data)
        note = "Some sessions/tests don't have subject information tracked." if has_unknown_subjects else None

        return Response({
            'student_id': student.id,
            'student_name': student.student_name,
            'study_sessions': subject_sessions,
            'test_history': test_data,
            'note': note
        })


class StudentGroupAPI(APIView):
    """
    Student Grouping System - Very Important Feature
    Teachers can create groups like: Weak in Fractions, Olympiad Batch, Remedial Batch, Fast Learners, Science Project Group

    Supports two URL patterns:
    1. /students/student-groups/ - General CRUD operations
    2. /teachers/groups/<teacher_id>/ - Teacher-specific group operations
    """

    def get(self, request, pk=None, teacher_id=None):
        """Get all groups, a specific group, or teacher-specific groups"""
        group_id = request.query_params.get('group_id')

        try:
            # If pk or group_id is provided, get specific group
            if pk or group_id:
                try:
                    group = StudentGroupModel.objects.get(id=pk or group_id)
                    serializer = StudentGroupSerializer(group)
                    return Response({
                        'status': True,
                        'data': serializer.data,
                        'message': 'Group retrieved successfully'
                    }, status=status.HTTP_200_OK)
                except StudentGroupModel.DoesNotExist:
                    return Response({
                        'status': False,
                        'message': 'Group not found'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Get all groups, optionally filtered by teacher
            if teacher_id:
                try:
                    teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
                except UserModel.DoesNotExist:
                    return Response({
                        'status': False,
                        'message': 'Teacher not found'
                    }, status=status.HTTP_404_NOT_FOUND)

                # Get students assigned to this teacher
                teacher_students = StudentModel.objects.filter(parent__id=teacher_id).distinct()
                # Get groups that contain these students
                groups = StudentGroupModel.objects.filter(
                    students__in=teacher_students
                ).distinct().order_by('-id')
            else:
                groups = StudentGroupModel.objects.all().order_by('-id')

            serializer = StudentGroupSerializer(groups, many=True)

            # Also include smart groups if teacher_id is provided
            response_data = {
                'status': True,
                'groups': serializer.data,
                'message': 'Groups retrieved successfully'
            }

            if teacher_id:
                teacher_students = StudentModel.objects.filter(parent__id=teacher_id).distinct()
                smart_groups = self._generate_smart_groups(teacher_students, teacher)
                response_data['smart_groups'] = smart_groups

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk=None, teacher_id=None):
        """Create a new group"""
        try:
            serializer = StudentGroupSerializer(data=request.data)
            if serializer.is_valid():
                # Optionally validate students belong to the teacher
                if teacher_id:
                    try:
                        teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
                        student_ids = request.data.get('student_ids', [])
                        teacher_students = StudentModel.objects.filter(
                            id__in=student_ids,
                            parent__id=teacher_id
                        ).distinct()

                        if teacher_students.count() != len(student_ids):
                            return Response({
                                'status': False,
                                'message': 'Some students do not belong to this teacher'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    except UserModel.DoesNotExist:
                        return Response({
                            'status': False,
                            'message': 'Teacher not found'
                        }, status=status.HTTP_404_NOT_FOUND)

                serializer.save()
                return Response({
                    'status': True,
                    'data': serializer.data,
                    'message': 'Group created successfully'
                }, status=status.HTTP_201_CREATED)

            return Response({
                'status': False,
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None, teacher_id=None):
        """Update an existing group"""
        group_id = pk or request.data.get('group_id') or request.query_params.get('group_id')

        if not group_id:
            return Response({
                'status': False,
                'message': 'group_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = StudentGroupModel.objects.get(id=group_id)
        except StudentGroupModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = StudentGroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': True,
                'data': serializer.data,
                'message': 'Group updated successfully'
            }, status=status.HTTP_200_OK)

        return Response({
            'status': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, teacher_id=None):
        """Delete a group"""
        group_id = pk or request.data.get('group_id') or request.query_params.get('group_id')

        if not group_id:
            return Response({
                'status': False,
                'message': 'group_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = StudentGroupModel.objects.get(id=group_id)
            group_name = group.name
            group.delete()
            return Response({
                'status': True,
                'message': f'Group "{group_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
        except StudentGroupModel.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def _generate_smart_groups(self, students, teacher):
        """Generate smart groups based on student performance"""
        groups = []

        # High Performers Group
        high_performers = []
        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            if attempts.exists():
                percentages = []
                for attempt in attempts:
                    if attempt.test.total_marks > 0:
                        percentage = (attempt.score / attempt.test.total_marks) * 100
                        percentages.append(percentage)
                if percentages:
                    avg_score = sum(percentages) / len(percentages)
                    if avg_score >= 80:
                        high_performers.append({'id': student.id, 'name': student.student_name, 'avg_score': round(avg_score, 2)})

        if high_performers:
            groups.append({
                'group_name': 'High Performers (80%+)',
                'student_count': len(high_performers),
                'students': high_performers,
                'type': 'performance_based'
            })

        # Struggling Students Group
        struggling_students = []
        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            if attempts.exists():
                percentages = []
                for attempt in attempts:
                    if attempt.test.total_marks > 0:
                        percentage = (attempt.score / attempt.test.total_marks) * 100
                        percentages.append(percentage)
                if percentages:
                    avg_score = sum(percentages) / len(percentages)
                    if avg_score < 60:
                        struggling_students.append({'id': student.id, 'name': student.student_name, 'avg_score': round(avg_score, 2)})

        if struggling_students:
            groups.append({
                'group_name': 'Needs Support (<60%)',
                'student_count': len(struggling_students),
                'students': struggling_students,
                'type': 'performance_based'
            })

        # Low Activity Group
        low_activity = []
        thirty_days_ago = timezone.now() - timedelta(days=30)
        for student in students:
            recent_sessions = StudySession.objects.filter(
                student=student,
                start_time__gte=thirty_days_ago
            )
            if recent_sessions.count() < 5:  # Less than 5 sessions in 30 days
                low_activity.append({'id': student.id, 'name': student.student_name, 'session_count': recent_sessions.count()})

        if low_activity:
            groups.append({
                'group_name': 'Low Activity (<5 sessions/30days)',
                'student_count': len(low_activity),
                'students': low_activity,
                'type': 'activity_based'
            })

        return groups


class TestSubmissionsAPI(APIView):
    """
    Gets submission status for tests created by the teacher
    """

    def get(self, request, teacher_id):
        # Get tests created by this teacher
        tests = TestModel.objects.filter(created_by__id=teacher_id).order_by('-created_at')

        assignment_data = []
        for test in tests:
            # Get submissions for this test
            submissions = StudentTestAttemptModel.objects.filter(test=test)
            submitted_count = submissions.count()
            total_students = test.student.count()

            # Calculate average score
            total_score = sum(submission.score for submission in submissions)
            average_score = (
                round(total_score / submitted_count, 2)
                if submitted_count > 0 else 0
            )

            assignment_data.append({
                'test_id': test.id,
                'title': test.title,
                'subject': test.subject.name if test.subject else "Unknown",
                'submitted_count': submitted_count,
                'total_students': total_students,
                'submission_rate': round((submitted_count / total_students) * 100, 2) if total_students > 0 else 0,
                'average_score': average_score,
                'total_marks': test.total_marks
            })

        return Response({
            'assignments': assignment_data
        })


class GroupAnalyticsAPI(APIView):
    # """
    # Group Analytics Page
    # For group: Weak in Algebra (12 students)
    # System shows: Group average, Improvement trend, Suggested test, Assign custom homework
    # """

    # def get(self, request, group_id):
    #     """Get analytics for a specific group"""
    #     try:
    #         group = StudentGroupModel.objects.get(id=group_id)
    #     except StudentGroupModel.DoesNotExist:
    #         return Response({
    #             'status': False,
    #             'message': 'Group not found'
    #         }, status=status.HTTP_404_NOT_FOUND)

    #     students = group.students.all()

    #     if not students.exists():
    #         return Response({
    #             'status': False,
    #             'message': 'No students in this group'
    #         }, status=status.HTTP_400_BAD_REQUEST)

    #     # Group performance metrics
    #     group_percentages = []
    #     subject_performance = {}
    #     improvement_data = []

    #     for student in students:
    #         attempts = StudentTestAttemptModel.objects.filter(student=student).order_by('started_at')
    #         if attempts.exists():
    #             # Current performance
    #             recent_attempts = attempts.order_by('-started_at')[:5]  # Last 5 tests
    #             recent_percentages = []
    #             for attempt in recent_attempts:
    #                 if attempt.test.total_marks > 0:
    #                     percentage = (attempt.score / attempt.test.total_marks) * 100
    #                     recent_percentages.append(percentage)

    #                     # Track by subject
    #                     subject_name = attempt.test.subject.name if attempt.test.subject else "Unknown"
    #                     if subject_name not in subject_performance:
    #                         subject_performance[subject_name] = []
    #                     subject_performance[subject_name].append(percentage)

    #             if recent_percentages:
    #                 student_avg = sum(recent_percentages) / len(recent_percentages)
    #                 group_percentages.append(student_avg)

    #             # Improvement trend (compare first half vs second half of attempts)
    #             if attempts.count() >= 4:
    #                 all_percentages = []
    #                 for attempt in attempts:
    #                     if attempt.test.total_marks > 0:
    #                         percentage = (attempt.score / attempt.test.total_marks) * 100
    #                         all_percentages.append(percentage)

    #                 if len(all_percentages) >= 4:
    #                     mid_point = len(all_percentages) // 2
    #                     first_half_avg = sum(all_percentages[:mid_point]) / mid_point
    #                     second_half_avg = sum(all_percentages[mid_point:]) / (len(all_percentages) - mid_point)
    #                     improvement = second_half_avg - first_half_avg

    #                     improvement_data.append({
    #                         'student_id': student.id,
    #                         'student_name': student.student_name,
    #                         'improvement': round(improvement, 2),
    #                         'trend': 'Improving' if improvement > 5 else 'Declining' if improvement < -5 else 'Stable'
    #                     })

    #     group_average = round(sum(group_percentages) / len(group_percentages), 2) if group_percentages else 0

    #     # Subject averages
    #     subject_averages = {}
    #     for subject, percentages in subject_performance.items():
    #         subject_averages[subject] = round(sum(percentages) / len(percentages), 2)

    #     # Overall improvement trend
    #     total_improvement = sum(item['improvement'] for item in improvement_data)
    #     avg_improvement = round(total_improvement / len(improvement_data), 2) if improvement_data else 0

    #     return Response({
    #         'status': True,
    #         'group_info': {
    #             'group_id': group.id,
    #             'group_name': group.name,
    #             'student_count': students.count(),
    #             'student_names': [s.student_name for s in students]
    #         },
    #         'performance_metrics': {
    #             'group_average': group_average,
    #             'subject_averages': subject_averages,
    #             'overall_improvement': avg_improvement,
    #             'improvement_trend': 'Positive' if avg_improvement > 2 else 'Negative' if avg_improvement < -2 else 'Stable'
    #         },
    #         'improvement_data': improvement_data,
    #         'suggestions': self._generate_suggestions(group_average, subject_averages, avg_improvement),
    #         'student_breakdown': [
    #             {
    #                 'student_id': student.id,
    #                 'student_name': student.student_name,
    #                 'class': student.student_class.get_display_name() if student.student_class else None
    #             } for student in students
    #         ]
    #     }, status=status.HTTP_200_OK)

    # def _generate_suggestions(self, group_average, subject_averages, improvement_trend):
    #     """Generate suggestions based on group performance"""
    #     suggestions = []
        
    #     if group_average < 60:
    #         suggestions.append("Consider assigning remedial materials and additional practice tests")
        
    #     if group_average > 85:
    #         suggestions.append("Group ready for advanced/challenging content")
        
    #     if improvement_trend < -2:
    #         suggestions.append("Review teaching methodology and provide additional support")
    #     elif improvement_trend > 5:
    #         suggestions.append("Current teaching approach is effective, continue with similar strategies")
        
    #     # Subject-specific suggestions
    #     for subject, avg in subject_averages.items():
    #         if avg < 50:
    #             suggestions.append(f"Focus intensive practice on {subject} - students struggling significantly")
    #         elif avg > 90:
    #             suggestions.append(f"{subject} performance excellent - consider advanced topics")

    #     if not suggestions:
    #         suggestions.append("Maintain current pace and monitor progress regularly")

    #     return suggestions
    """
    Group Analytics Page
    GET  /api/groups/<group_id>/analytics/
    POST /api/groups/<group_id>/analytics/?action=assign_homework   — assign homework
    POST /api/groups/<group_id>/analytics/?action=suggested_tests   — get suggestions
    """
 
    def get(self, request, group_id):
        try:
            group = StudentGroupModel.objects.get(id=group_id)
        except StudentGroupModel.DoesNotExist:
            return Response({'status': False, 'message': 'Group not found'},
                            status=status.HTTP_404_NOT_FOUND)
 
        students = group.students.all()
        if not students.exists():
            return Response({'status': False, 'message': 'No students in this group'},
                            status=status.HTTP_400_BAD_REQUEST)
 
        group_percentages = []
        subject_performance = {}
        improvement_data = []
 
        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(
                student=student
            ).order_by('started_at')
 
            if attempts.exists():
                recent_attempts = attempts.order_by('-started_at')[:5]
                recent_percentages = []
                for attempt in recent_attempts:
                    if attempt.test.total_marks > 0:
                        pct = (attempt.score / attempt.test.total_marks) * 100
                        recent_percentages.append(pct)
                        subject_name = attempt.test.subject.name if attempt.test.subject else 'Unknown'
                        subject_performance.setdefault(subject_name, []).append(pct)
 
                if recent_percentages:
                    group_percentages.append(
                        sum(recent_percentages) / len(recent_percentages)
                    )
 
                if attempts.count() >= 4:
                    all_pcts = [
                        (a.score / a.test.total_marks) * 100
                        for a in attempts if a.test.total_marks > 0
                    ]
                    if len(all_pcts) >= 4:
                        mid = len(all_pcts) // 2
                        first_avg  = sum(all_pcts[:mid]) / mid
                        second_avg = sum(all_pcts[mid:]) / (len(all_pcts) - mid)
                        improvement = second_avg - first_avg
                        improvement_data.append({
                            'student_id':   student.id,
                            'student_name': student.student_name,
                            'improvement':  round(improvement, 2),
                            'trend': (
                                'Improving'  if improvement > 5 else
                                'Declining'  if improvement < -5 else
                                'Stable'
                            ),
                        })
 
        group_average = (
            round(sum(group_percentages) / len(group_percentages), 2)
            if group_percentages else 0
        )
        subject_averages = {
            s: round(sum(v) / len(v), 2) for s, v in subject_performance.items()
        }
        avg_improvement = (
            round(sum(i['improvement'] for i in improvement_data) / len(improvement_data), 2)
            if improvement_data else 0
        )
 
        # ── Pending homework assigned to this group ──────────────────────────
        pending_homework = HomeworkModel.objects.filter(
            group=group
        ).order_by('-created_at')[:5]
 
        homework_summary = [{
            'id':        hw.id,
            'title':     hw.title,
            'subject':   hw.subject.name if hw.subject else None,
            'due_date':  hw.due_date,
            'total_assigned': hw.assigned_to.count(),
            'submissions':    hw.submissions.filter(
                submitted_at__isnull=False
            ).count(),
        } for hw in pending_homework]
 
        # ── Suggested tests (quick preview — full list via separate endpoint) ─
        suggestions_result = SuggestedTestSerializer.get_suggestions(group_id)
        top_suggestions = (
            suggestions_result.get('suggestions', [])[:3]
            if suggestions_result else []
        )
 
        return Response({
            'status': True,
            'group_info': {
                'group_id':     group.id,
                'group_name':   group.name,
                'student_count': students.count(),
                'student_names': [s.student_name for s in students],
            },
            'performance_metrics': {
                'group_average':      group_average,
                'subject_averages':   subject_averages,
                'overall_improvement': avg_improvement,
                'improvement_trend': (
                    'Positive' if avg_improvement > 2 else
                    'Negative' if avg_improvement < -2 else
                    'Stable'
                ),
            },
            'improvement_data': improvement_data,
            'suggestions':  self._generate_suggestions(
                group_average, subject_averages, avg_improvement
            ),
            # ── NEW: homework & suggested-test previews ──────────────────────
            'assigned_homework': homework_summary,
            'suggested_tests':   top_suggestions,
            'actions': {
                'assign_homework_url':  f'/api/homework/create/',
                'suggested_tests_url':  f'/api/groups/{group_id}/suggested-tests/',
                'assign_hw_to_group_url': f'/api/homework/<homework_id>/assign-group/',
            },
            'student_breakdown': [{
                'student_id':   s.id,
                'student_name': s.student_name,
                'class': s.student_class.get_display_name() if s.student_class else None,
            } for s in students],
        }, status=status.HTTP_200_OK)
 
    # POST: assign existing homework OR get suggested tests
    def post(self, request, group_id):
        action = request.query_params.get('action', '')
 
        try:
            group = StudentGroupModel.objects.get(id=group_id)
        except StudentGroupModel.DoesNotExist:
            return Response({'status': False, 'message': 'Group not found'},
                            status=status.HTTP_404_NOT_FOUND)
 
        # ── Action 1: assign homework to this group ──────────────────────────
        if action == 'assign_homework':
            homework_id = request.data.get('homework_id')
            if not homework_id:
                return Response(
                    {'status': False, 'message': 'homework_id is required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                homework = HomeworkModel.objects.get(id=homework_id)
            except HomeworkModel.DoesNotExist:
                return Response({'status': False, 'message': 'Homework not found'},
                                status=status.HTTP_404_NOT_FOUND)
 
            student_ids = group.students.values_list('id', flat=True)
            homework.assigned_to.add(*student_ids)
            homework.group = group
            homework.save()
 
            return Response({
                'status': True,
                'message': f'Homework "{homework.title}" assigned to group "{group.name}"',
                'homework_id':    homework.id,
                'group_id':       group.id,
                'total_assigned': homework.assigned_to.count(),
            }, status=status.HTTP_200_OK)
 
        # ── Action 2: create NEW homework for this group ─────────────────────
        if action == 'create_homework':
            serializer = HomeworkCreateSerializer(
                data=request.data, context={'request': request}
            )
            if serializer.is_valid():
                homework = serializer.save()
                # Also wire up the group
                student_ids = group.students.values_list('id', flat=True)
                homework.assigned_to.add(*student_ids)
                homework.group = group
                homework.save()
                return Response({
                    'status': True,
                    'message': 'Homework created and assigned to group',
                    'homework_id':    homework.id,
                    'total_assigned': homework.assigned_to.count(),
                }, status=status.HTTP_201_CREATED)
            return Response({'status': False, 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
 
        # ── Action 3: get full suggested tests ───────────────────────────────
        if action == 'suggested_tests':
            result = SuggestedTestSerializer.get_suggestions(group_id)
            if result is None:
                return Response({'status': False, 'message': 'Group not found'},
                                status=status.HTTP_404_NOT_FOUND)
            return Response({'status': True, **result}, status=status.HTTP_200_OK)
 
        return Response(
            {'status': False, 'message': 'Unknown action. Use assign_homework, create_homework, or suggested_tests.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
 
    def _generate_suggestions(self, group_average, subject_averages, improvement_trend):
        suggestions = []
        if group_average < 60:
            suggestions.append(
                'Consider assigning remedial materials and additional practice tests'
            )
        if group_average > 85:
            suggestions.append('Group ready for advanced/challenging content')
        if improvement_trend < -2:
            suggestions.append(
                'Review teaching methodology and provide additional support'
            )
        elif improvement_trend > 5:
            suggestions.append(
                'Current teaching approach is effective, continue with similar strategies'
            )
        for subject, avg in subject_averages.items():
            if avg < 50:
                suggestions.append(
                    f'Focus intensive practice on {subject} — students struggling significantly'
                )
            elif avg > 90:
                suggestions.append(
                    f'{subject} performance excellent — consider advanced topics'
                )
        if not suggestions:
            suggestions.append('Maintain current pace and monitor progress regularly')
        return suggestions

class StudentComparisonAPI(APIView):
    # """
    # Student Comparison System
    # Inside Class Analytics: Comparison Mode
    # Select students: ☑ Aarav ☑ Rohan ☑ Myra
    # Click Compare → System shows: Score comparison, Growth comparison, Accuracy comparison, Topic mastery comparison
    # """

    # def get(self, request):
    #     student_ids = request.GET.get('student_ids', '').split(',')
    #     subject_id = request.GET.get('subject')
    #     date_range = request.GET.get('date_range', '30')
        
    #     student_ids = [int(sid) for sid in student_ids if sid.isdigit()]
        
    #     if len(student_ids) < 2:
    #         return Response({'error': 'At least 2 students required for comparison'}, status=400)

    #     students = StudentModel.objects.filter(id__in=student_ids)
    #     if students.count() != len(student_ids):
    #         return Response({'error': 'Some students not found'}, status=404)

    #     comparison_data = []
        
    #     for student in students:
    #         # Get test attempts
    #         attempts = StudentTestAttemptModel.objects.filter(student=student)
    #         if subject_id:
    #             attempts = attempts.filter(test__subject_id=subject_id)
            
    #         if attempts.exists():
    #             # Score comparison
    #             percentages = []
    #             for attempt in attempts:
    #                 if attempt.test.total_marks > 0:
    #                     percentage = (attempt.score / attempt.test.total_marks) * 100
    #                     percentages.append(percentage)
                
    #             avg_score = round(sum(percentages) / len(percentages), 2) if percentages else 0
                
    #             # Growth comparison (first half vs second half)
    #             sorted_attempts = attempts.order_by('started_at')
    #             all_percentages = []
    #             for attempt in sorted_attempts:
    #                 if attempt.test.total_marks > 0:
    #                     percentage = (attempt.score / attempt.test.total_marks) * 100
    #                     all_percentages.append(percentage)
                
    #             growth = 0
    #             if len(all_percentages) >= 4:
    #                 mid_point = len(all_percentages) // 2
    #                 first_avg = sum(all_percentages[:mid_point]) / mid_point
    #                 second_avg = sum(all_percentages[mid_point:]) / (len(all_percentages) - mid_point)
    #                 growth = round(second_avg - first_avg, 2)
                
    #             # Accuracy comparison (correct answers)
    #             total_questions = 0
    #             correct_answers = 0
    #             for attempt in attempts:
    #                 answers = StudentAnswerModel.objects.filter(attempt=attempt)
    #                 total_questions += answers.count()
    #                 correct_answers += answers.filter(selected_option__is_correct=True).count()
                
    #             accuracy = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0
                
    #             comparison_data.append({
    #                 'student_id': student.id,
    #                 'student_name': student.student_name,
    #                 'class': student.student_class.get_display_name() if student.student_class else None,
    #                 'average_score': avg_score,
    #                 'growth': growth,
    #                 'accuracy': accuracy,
    #                 'test_count': attempts.count(),
    #                 'total_questions': total_questions,
    #                 'correct_answers': correct_answers
    #             })

    #     # Sort by average score for ranking
    #     comparison_data.sort(key=lambda x: x['average_score'], reverse=True)
        
    #     # Add rankings
    #     for i, student_data in enumerate(comparison_data):
    #         student_data['rank'] = i + 1

    #     return Response({
    #         'comparison_data': comparison_data,
    #         'subject': Subject.objects.get(id=subject_id).name if subject_id else 'All Subjects',
    #         'date_range': f"Last {date_range} days",
    #         'total_students_compared': len(comparison_data)
    #     })
    """
    Student Comparison
    GET /api/students/compare/?student_ids=1,2,3&subject=<id>
 
    FIXED: topic_mastery breakdown is now populated (was missing).
    """
 
    def get(self, request):
        student_ids_raw = request.GET.get('student_ids', '').split(',')
        subject_id  = request.GET.get('subject')
        date_range  = request.GET.get('date_range', '30')
 
        student_ids = [int(s) for s in student_ids_raw if s.strip().isdigit()]
        if len(student_ids) < 2:
            return Response(
                {'error': 'At least 2 students required for comparison'}, status=400
            )
 
        students = StudentModel.objects.filter(id__in=student_ids)
        if students.count() != len(student_ids):
            return Response({'error': 'Some students not found'}, status=404)
 
        comparison_data = []
 
        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            if subject_id:
                attempts = attempts.filter(test__subject_id=subject_id)
 
            if not attempts.exists():
                comparison_data.append({
                    'student_id':    student.id,
                    'student_name':  student.student_name,
                    'class':         student.student_class.get_display_name() if student.student_class else None,
                    'average_score': 0,
                    'growth':        0,
                    'accuracy':      0,
                    'test_count':    0,
                    'total_questions':  0,
                    'correct_answers':  0,
                    'topic_mastery':    [],
                })
                continue
 
            # Score
            pcts = [
                (a.score / a.test.total_marks) * 100
                for a in attempts if a.test.total_marks > 0
            ]
            avg_score = round(sum(pcts) / len(pcts), 2) if pcts else 0
 
            # Growth (first half vs second half)
            sorted_attempts = attempts.order_by('started_at')
            all_pcts = [
                (a.score / a.test.total_marks) * 100
                for a in sorted_attempts if a.test.total_marks > 0
            ]
            growth = 0
            if len(all_pcts) >= 4:
                mid        = len(all_pcts) // 2
                first_avg  = sum(all_pcts[:mid]) / mid
                second_avg = sum(all_pcts[mid:]) / (len(all_pcts) - mid)
                growth     = round(second_avg - first_avg, 2)
 
            # Accuracy
            total_q = correct_q = 0
            for attempt in attempts:
                answers  = StudentAnswerModel.objects.filter(attempt=attempt)
                total_q += answers.count()
                correct_q += answers.filter(selected_option__is_correct=True).count()
            accuracy = round((correct_q / total_q) * 100, 2) if total_q > 0 else 0
 
            # ── TOPIC MASTERY (new) ───────────────────────────────────────────
            # Groups questions by test, computes per-topic (per-question) accuracy.
            # "Topic" here = individual question. For richer grouping you would add
            # a topic/chapter FK to QuestionsModel; this is the correct fallback.
            topic_mastery = []
            questions_seen = QuestionsModel.objects.filter(
                test__in=attempts.values('test')
            ).distinct()
 
            for question in questions_seen[:20]:  # cap at 20 to keep response lean
                q_answers = StudentAnswerModel.objects.filter(
                    attempt__in=attempts,
                    question=question,
                )
                q_total   = q_answers.count()
                q_correct = q_answers.filter(
                    selected_option__is_correct=True
                ).count()
                if q_total == 0:
                    continue
                q_accuracy = round((q_correct / q_total) * 100, 2)
                q_text     = question.question_text or ''
                topic_mastery.append({
                    'question_id':   question.id,
                    'question_text': (
                        q_text[:80] + '...' if len(q_text) > 80 else q_text
                    ),
                    'subject': (
                        question.test.subject.name
                        if question.test.subject else 'Unknown'
                    ),
                    'accuracy':         q_accuracy,
                    'attempts':         q_total,
                    'correct':          q_correct,
                    'mastery_level': (
                        'Mastered'    if q_accuracy >= 80 else
                        'Developing'  if q_accuracy >= 50 else
                        'Struggling'
                    ),
                })
 
            # Sort: struggling first so comparison is most informative
            topic_mastery.sort(key=lambda x: x['accuracy'])
 
            comparison_data.append({
                'student_id':    student.id,
                'student_name':  student.student_name,
                'class':         student.student_class.get_display_name() if student.student_class else None,
                'average_score': avg_score,
                'growth':        growth,
                'accuracy':      accuracy,
                'test_count':    attempts.count(),
                'total_questions':  total_q,
                'correct_answers':  correct_q,
                'topic_mastery':    topic_mastery,   # ← NOW POPULATED
            })
 
        # Sort by average score for ranking
        comparison_data.sort(key=lambda x: x['average_score'], reverse=True)
        for i, d in enumerate(comparison_data):
            d['rank'] = i + 1
 
        # Shared weak topics (appear in multiple students' struggling list)
        all_struggling_ids = defaultdict(int)
        for d in comparison_data:
            for t in d['topic_mastery']:
                if t['mastery_level'] == 'Struggling':
                    all_struggling_ids[t['question_id']] += 1
 
        shared_weak_topics = [
            qid for qid, count in all_struggling_ids.items()
            if count >= 2
        ]
 
        return Response({
            'comparison_data':      comparison_data,
            'subject': (
                Subject.objects.get(id=subject_id).name
                if subject_id else 'All Subjects'
            ),
            'date_range':              f'Last {date_range} days',
            'total_students_compared': len(comparison_data),
            'shared_weak_topic_ids':   shared_weak_topics,  # questions both/all struggle with
        })
 

class AdvancedFilterAPI(APIView):
    """
    Advanced Filter System (Top Bar)
    Filters: Class, Section, Subject, Group, Date Range, Difficulty Level
    Without filter system → Panel becomes messy
    """

    def get(self, request, teacher_id):
        filter_type = request.GET.get('filter_type')  # 'class', 'subject', 'date_range', etc.

        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        # Get teacher's assigned classes and subjects from TeacherAssignmentModel
        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = teacher_assignment.assigned_classes.all()
            assigned_subjects = teacher_assignment.assigned_subjects.all()
        except TeacherAssignmentModel.DoesNotExist:
            # Fallback: Get from students and tests
            students = StudentModel.objects.filter(parent__id=teacher_id).distinct()
            assigned_classes = ClassModel.objects.filter(students__in=students).distinct()
            assigned_subjects = Subject.objects.filter(testmodel__created_by=teacher).distinct()

        if filter_type == 'class':
            return Response({
                'filter_type': 'class',
                'options': [{'value': c.id, 'label': c.get_display_name()} for c in assigned_classes]
            })

        elif filter_type == 'subject':
            return Response({
                'filter_type': 'subject',
                'options': [{'value': s.id, 'label': s.name} for s in assigned_subjects]
            })

        elif filter_type == 'date_range':
            return Response({
                'filter_type': 'date_range',
                'options': [
                    {'value': '7', 'label': 'Last 7 days'},
                    {'value': '30', 'label': 'Last 30 days'},
                    {'value': '90', 'label': 'Last 90 days'},
                    {'value': '365', 'label': 'Last year'}
                ]
            })

        elif filter_type == 'difficulty':
            return Response({
                'filter_type': 'difficulty',
                'options': [
                    {'value': 'easy', 'label': 'Easy'},
                    {'value': 'medium', 'label': 'Medium'},
                    {'value': 'hard', 'label': 'Hard'},
                    {'value': 'mixed', 'label': 'Mixed'}
                ]
            })

        else:
            # Return all available filters
            return Response({
                'filters': {
                    'class': [{'value': c.id, 'label': c.get_display_name()} for c in assigned_classes],
                    'subject': [{'value': s.id, 'label': s.name} for s in assigned_subjects],
                    'date_range': [
                        {'value': '7', 'label': 'Last 7 days'},
                        {'value': '30', 'label': 'Last 30 days'},
                        {'value': '90', 'label': 'Last 90 days'},
                        {'value': '365', 'label': 'Last year'}
                    ],
                    'difficulty': [
                        {'value': 'easy', 'label': 'Easy'},
                        {'value': 'medium', 'label': 'Medium'},
                        {'value': 'hard', 'label': 'Hard'},
                        {'value': 'mixed', 'label': 'Mixed'}
                    ]
                }
            })


class CrossSubjectOverviewAPI(APIView):
    """
    Cross Subject Overview (Restricted)
    Math teacher can see: Overall academic health score
    But detailed subject analytics only for their subject
    This prevents confusion.
    """

    def get(self, request, teacher_id):
        student_id = request.GET.get('student_id')
        class_id = request.GET.get('class_id')  # Changed from class_name to class_id

        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        # Get teacher's assigned classes and subjects
        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = teacher_assignment.assigned_classes.all()
            teacher_subjects = teacher_assignment.assigned_subjects.all()
        except TeacherAssignmentModel.DoesNotExist:
            # Fallback
            students_fallback = StudentModel.objects.filter(parent__id=teacher_id).distinct()
            assigned_classes = ClassModel.objects.filter(students__in=students_fallback).distinct()
            teacher_subjects = Subject.objects.filter(testmodel__created_by=teacher).distinct()

        # Get students from assigned classes
        students = StudentModel.objects.filter(student_class__in=assigned_classes)

        if student_id:
            students = students.filter(id=student_id)

        if class_id:
            students = students.filter(student_class__id=class_id)

        if not students.exists():
            return Response({'error': 'No students found'}, status=404)

        overview_data = []

        for student in students:
            # Get all test attempts for this student
            all_attempts = StudentTestAttemptModel.objects.filter(student=student)

            # Get teacher's subject attempts only
            teacher_attempts = all_attempts.filter(test__subject__in=teacher_subjects)

            # Overall academic health score (all subjects)
            all_percentages = []
            for attempt in all_attempts:
                if attempt.test.total_marks > 0:
                    percentage = (attempt.score / attempt.test.total_marks) * 100
                    all_percentages.append(percentage)

            overall_health = round(sum(all_percentages) / len(all_percentages), 2) if all_percentages else 0

            # Teacher's subject performance
            teacher_percentages = []
            for attempt in teacher_attempts:
                if attempt.test.total_marks > 0:
                    percentage = (attempt.score / attempt.test.total_marks) * 100
                    teacher_percentages.append(percentage)

            teacher_subject_avg = round(sum(teacher_percentages) / len(teacher_percentages), 2) if teacher_percentages else 0

            # Subject breakdown
            subject_breakdown = {}
            for subject in teacher_subjects:
                subject_attempts = all_attempts.filter(test__subject=subject)
                if subject_attempts.exists():
                    subject_percentages = []
                    for attempt in subject_attempts:
                        if attempt.test.total_marks > 0:
                            percentage = (attempt.score / attempt.test.total_marks) * 100
                            subject_percentages.append(percentage)
                    if subject_percentages:
                        subject_breakdown[subject.name] = round(sum(subject_percentages) / len(subject_percentages), 2)

            overview_data.append({
                'student_id': student.id,
                'student_name': student.student_name,
                'class': student.student_class.get_display_name() if student.student_class else None,
                'overall_academic_health': overall_health,  # Restricted overview
                'teacher_subject_average': teacher_subject_avg,  # Detailed analytics for teacher's subject
                'subject_breakdown': subject_breakdown,  # Only teacher's subjects
                'total_tests_taken': all_attempts.count(),
                'teacher_subject_tests': teacher_attempts.count()
            })

        return Response({
            'teacher_info': {
                'id': teacher.id,
                'name': f"{teacher.first_name} {teacher.last_name}",
                'subjects': [s.name for s in teacher_subjects]
            },
            'students_overview': overview_data,
            'restricted_access': True  # Indicates this is a restricted view
        })


# ============================================================================
# NEW TEACHER APIs - Phase 2
# ============================================================================

class BatchManagementAPI(APIView):
    """
    Batch/Section Management for tuitions
    Morning/Evening batches, timing, days
    """

    def get(self, request, teacher_id=None):
        """List teacher's batches"""
        try:
            from user_management.models import BatchModel
        except ImportError:
            return Response({
                "error": "BatchModel not yet migrated. Please run migrations."
            }, status=400)

        if not teacher_id:
            teacher_id = request.user.id

        batches = BatchModel.objects.filter(teacher_id=teacher_id, is_active=True)

        batches_data = []
        for batch in batches:
            student_count = batch.students.count()

            # Get batch performance
            students = batch.students.all()
            all_percentages = []
            for student in students:
                attempts = StudentTestAttemptModel.objects.filter(student=student)
                for a in attempts:
                    if a.test.total_marks > 0:
                        all_percentages.append((a.score / a.test.total_marks) * 100)

            avg_performance = round(sum(all_percentages) / len(all_percentages), 1) if all_percentages else 0

            # Get class display (handle both old and new models)
            class_display = None
            class_id = None
            if batch.class_ref:
                class_display = batch.class_ref.get_display_name()
                class_id = batch.class_ref.id
            elif batch.student_class:
                class_display = f"Class {batch.student_class}"
                class_id = None

            batches_data.append({
                "id": batch.id,
                "name": batch.name,
                "timing": batch.timing,
                "days": batch.days,
                "class_id": class_id,
                "class_display": class_display,
                "student_class_legacy": batch.student_class,  # Keep for backward compatibility
                "subject": batch.subject.name if batch.subject else None,
                "subject_id": batch.subject.id if batch.subject else None,
                "student_count": student_count,
                "avg_performance": avg_performance,
                "created_at": batch.created_at
            })

        return Response({
            "batches": batches_data,
            "total_batches": len(batches_data)
        })

    def post(self, request):
        """Create a new batch"""
        try:
            from user_management.models import BatchModel
        except ImportError:
            return Response({
                "error": "BatchModel not yet migrated."
            }, status=400)

        data = request.data
        teacher_id = data.get('teacher_id', request.user.id)

        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({"error": "Teacher not found"}, status=404)

        # Get subject if provided
        subject = None
        if 'subject_id' in data:
            try:
                subject = Subject.objects.get(id=data['subject_id'])
            except Subject.DoesNotExist:
                pass

        # Get class_ref if provided
        class_ref = None
        if 'class_id' in data:
            try:
                class_ref = ClassModel.objects.get(id=data['class_id'])
            except ClassModel.DoesNotExist:
                return Response({"error": "Class not found"}, status=404)

        batch = BatchModel.objects.create(
            name=data.get('name', 'New Batch'),
            teacher=teacher,
            timing=data.get('timing'),
            days=data.get('days', []),
            class_ref=class_ref,
            student_class=data.get('student_class'),  # Legacy support
            subject=subject
        )

        # Add students if provided
        if 'student_ids' in data:
            students = StudentModel.objects.filter(id__in=data['student_ids'])
            batch.students.set(students)

        return Response({
            "message": "Batch created successfully",
            "batch_id": batch.id
        }, status=201)

    def put(self, request, batch_id=None):
        """Update a batch"""
        try:
            from user_management.models import BatchModel
        except ImportError:
            return Response({"error": "BatchModel not yet migrated."}, status=400)

        if not batch_id:
            batch_id = request.data.get('batch_id')

        try:
            batch = BatchModel.objects.get(id=batch_id)
        except BatchModel.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

        data = request.data

        if 'name' in data:
            batch.name = data['name']
        if 'timing' in data:
            batch.timing = data['timing']
        if 'days' in data:
            batch.days = data['days']
        if 'class_id' in data:
            # Use new ClassModel
            try:
                batch.class_ref = ClassModel.objects.get(id=data['class_id'])
            except ClassModel.DoesNotExist:
                return Response({"error": "Class not found"}, status=404)
        if 'student_class' in data:
            # Legacy support
            batch.student_class = data['student_class']
        if 'is_active' in data:
            batch.is_active = data['is_active']
        if 'student_ids' in data:
            students = StudentModel.objects.filter(id__in=data['student_ids'])
            batch.students.set(students)

        batch.save()

        return Response({"message": "Batch updated successfully"})

    def delete(self, request, batch_id=None):
        """Delete (deactivate) a batch"""
        try:
            from user_management.models import BatchModel
        except ImportError:
            return Response({"error": "BatchModel not yet migrated."}, status=400)

        if not batch_id:
            batch_id = request.data.get('batch_id')

        try:
            batch = BatchModel.objects.get(id=batch_id)
            batch.is_active = False
            batch.save()
            return Response({"message": "Batch deactivated successfully"})
        except BatchModel.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

class BatchDetailAPI(APIView):
    def get(self, request, batch_id):
        try:
            batch = BatchModel.objects.get(id=batch_id, is_active=True)
        except BatchModel.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

        # Build batch data similar to BatchManagementAPI.get()
        student_count = batch.students.count()
        students = batch.students.all()
        all_percentages = []
        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            for a in attempts:
                if a.test.total_marks > 0:
                    all_percentages.append((a.score / a.test.total_marks) * 100)
        avg_performance = round(sum(all_percentages) / len(all_percentages), 1) if all_percentages else 0

        class_display = None
        class_id = None
        if batch.class_ref:
            class_display = batch.class_ref.get_display_name()
            class_id = batch.class_ref.id
        elif batch.student_class:
            class_display = f"Class {batch.student_class}"

        batch_data = {
            "id": batch.id,
            "name": batch.name,
            "timing": batch.timing,
            "days": batch.days,
            "class_id": class_id,
            "class_display": class_display,
            "student_class_legacy": batch.student_class,
            "subject": batch.subject.name if batch.subject else None,
            "subject_id": batch.subject.id if batch.subject else None,
            "student_count": student_count,
            "avg_performance": avg_performance,
            "created_at": batch.created_at
        }

        return Response(batch_data)
        
class BatchAnalyticsAPI(APIView):
    """
    Batch Performance Analytics
    Shows: batch average, subject performance, improvement trends
    """

    def get(self, request, batch_id):
        try:
            from user_management.models import BatchModel
        except ImportError:
            return Response({"error": "BatchModel not yet migrated."}, status=400)

        try:
            batch = BatchModel.objects.get(id=batch_id)
        except BatchModel.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

        students = batch.students.all()
        now = timezone.now()
        last30 = now - timedelta(days=30)

        # Collect performance data
        student_data = []
        all_percentages = []
        subject_scores = defaultdict(list)

        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(
                student=student,
                started_at__gte=last30
            )

            percentages = []
            for a in attempts:
                if a.test.total_marks > 0:
                    pct = (a.score / a.test.total_marks) * 100
                    percentages.append(pct)
                    all_percentages.append(pct)
                    
                    if a.test.subject:
                        subject_scores[a.test.subject.name].append(pct)

            # Study sessions
            sessions = StudySession.objects.filter(
                student=student,
                start_time__gte=last30
            )
            study_hours = sum(s.duration or 0 for s in sessions) / 60

            avg_score = sum(percentages) / len(percentages) if percentages else 0

            student_data.append({
                "student_id": student.id,
                "name": student.student_name,
                "class": student.student_class,
                "avg_score": round(avg_score, 1),
                "tests_taken": len(percentages),
                "study_hours": round(study_hours, 1)
            })

        # Sort by average score
        student_data.sort(key=lambda x: x["avg_score"], reverse=True)

        # Calculate batch averages
        batch_avg = round(sum(all_percentages) / len(all_percentages), 1) if all_percentages else 0

        # Subject performance
        subject_performance = {}
        for subject, scores in subject_scores.items():
            subject_performance[subject] = round(sum(scores) / len(scores), 1)

        # Top performers
        top_performers = student_data[:3] if len(student_data) >= 3 else student_data

        # Needs attention
        needs_attention = [s for s in student_data if s["avg_score"] < 60]

        return Response({
            "batch_info": {
                "id": batch.id,
                "name": batch.name,
                "timing": batch.timing,
                "days": batch.days,
                "student_count": len(students)
            },
            "performance": {
                "batch_average": batch_avg,
                "subject_breakdown": subject_performance,
                "total_tests_last_30d": len(all_percentages)
            },
            "students": student_data,
            "top_performers": top_performers,
            "needs_attention": needs_attention,
            "attention_count": len(needs_attention)
        })


class HomeworkAPI(APIView):
    """
    Homework Assignment API
    Create, list, and manage homework (separate from tests)
    """

    def get(self, request, teacher_id=None):
        """List teacher's homework assignments"""
        try:
            from user_management.models import HomeworkModel
        except ImportError:
            return Response({
                "error": "HomeworkModel not yet migrated."
            }, status=400)

        if not teacher_id:
            teacher_id = request.user.id

        homework_list = HomeworkModel.objects.filter(
            created_by_id=teacher_id
        ).order_by('-created_at')

        homework_data = []
        now = timezone.now()

        for hw in homework_list:
            # Count submissions
            total_assigned = hw.assigned_to.count()
            submissions = hw.submissions.filter(submitted_at__isnull=False).count()
            
            # Calculate average score
            scored_submissions = hw.submissions.exclude(score__isnull=True)
            avg_score = None
            if scored_submissions.exists():
                scores = [s.score for s in scored_submissions]
                avg_score = round(sum(scores) / len(scores), 1)

            # Status
            if now > hw.due_date:
                status = "completed"
            else:
                status = "active"

            homework_data.append({
                "id": hw.id,
                "title": hw.title,
                "subject": hw.subject.name if hw.subject else None,
                "description": hw.description,
                "due_date": hw.due_date,
                "total_marks": hw.total_marks,
                "batch_id": hw.batch_id,
                "batch_name": hw.batch.name if hw.batch else None,
                "total_assigned": total_assigned,
                "submissions_count": submissions,
                "submission_rate": round((submissions / total_assigned) * 100, 1) if total_assigned > 0 else 0,
                "avg_score": avg_score,
                "status": status,
                "created_at": hw.created_at
            })

        return Response({
            "homework": homework_data,
            "total_homework": len(homework_data)
        })

    # def post(self, request):
    #     """Create homework assignment"""
    #     try:
    #         from user_management.models import HomeworkModel, BatchModel
    #     except ImportError:
    #         return Response({"error": "Models not yet migrated."}, status=400)

    #     data = request.data

    #     required_fields = ['title', 'due_date']
    #     for field in required_fields:
    #         if field not in data:
    #             return Response({"error": f"Missing required field: {field}"}, status=400)

    #     # Get subject
    #     subject = None
    #     if 'subject_id' in data:
    #         try:
    #             subject = Subject.objects.get(id=data['subject_id'])
    #         except Subject.DoesNotExist:
    #             pass

    #     # Get batch
    #     batch = None
    #     if 'batch_id' in data:
    #         try:
    #             batch = BatchModel.objects.get(id=data['batch_id'])
    #         except BatchModel.DoesNotExist:
    #             pass

    #     homework = HomeworkModel.objects.create(
    #         title=data['title'],
    #         subject=subject,
    #         description=data.get('description'),
    #         due_date=data['due_date'],
    #         batch=batch,
    #         total_marks=data.get('total_marks', 100),
    #         created_by=request.user
    #     )

    #     # Assign students
    #     if 'student_ids' in data:
    #         students = StudentModel.objects.filter(id__in=data['student_ids'])
    #         homework.assigned_to.set(students)
    #     elif batch:
    #         # Assign all students in the batch
    #         homework.assigned_to.set(batch.students.all())

    #     return Response({
    #         "message": "Homework created successfully",
    #         "homework_id": homework.id
    #     }, status=201)

    def post(self, request):
        data = request.data
 
        required_fields = ['title', 'due_date']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Missing required field: {field}'}, status=400
                )
 
        subject = None
        if 'subject_id' in data:
            try:
                subject = Subject.objects.get(id=data['subject_id'])
            except Subject.DoesNotExist:
                pass
 
        from user_management.models import BatchModel  # local import for safety
        batch = None
        if 'batch_id' in data:
            try:
                batch = BatchModel.objects.get(id=data['batch_id'])
            except BatchModel.DoesNotExist:
                pass
 
        # ── group_id support (NEW) ───────────────────────────────────────────
        group = None
        if 'group_id' in data:
            try:
                group = StudentGroupModel.objects.get(id=data['group_id'])
            except StudentGroupModel.DoesNotExist:
                return Response(
                    {'error': f'Group with id {data["group_id"]} not found'}, status=404
                )
 
        homework = HomeworkModel.objects.create(
            title=data['title'],
            subject=subject,
            description=data.get('description'),
            due_date=data['due_date'],
            batch=batch,
            total_marks=data.get('total_marks', 100),
            created_by=request.user if request.user.is_authenticated else None,
        )
 
        # Priority: explicit student_ids > group > batch
        if 'student_ids' in data:
            students = StudentModel.objects.filter(id__in=data['student_ids'])
            homework.assigned_to.set(students)
        elif group:
            homework.assigned_to.set(group.students.all())
            homework.group = group  # wire the FK
            homework.save(update_fields=['group'])
        elif batch:
            homework.assigned_to.set(batch.students.all())
 
        return Response({
            'message':        'Homework created successfully',
            'homework_id':    homework.id,
            'assigned_to':    homework.assigned_to.count(),
            'group_assigned': group.name if group else None,
            'batch_assigned': batch.name if batch else None,
        }, status=201)
    
    def delete(self, request, homework_id=None):
        """Delete homework"""
        try:
            from user_management.models import HomeworkModel
        except ImportError:
            return Response({"error": "HomeworkModel not yet migrated."}, status=400)

        if not homework_id:
            homework_id = request.data.get('homework_id')

        try:
            homework = HomeworkModel.objects.get(id=homework_id)
            homework.delete()
            return Response({"message": "Homework deleted successfully"})
        except HomeworkModel.DoesNotExist:
            return Response({"error": "Homework not found"}, status=404)


class HomeworkSubmissionsAPI(APIView):
    """
    View and grade homework submissions
    """

    def get(self, request, homework_id):
        """Get all submissions for a homework"""
        try:
            from user_management.models import HomeworkModel, HomeworkSubmissionModel
        except ImportError:
            return Response({"error": "Models not yet migrated."}, status=400)

        try:
            homework = HomeworkModel.objects.get(id=homework_id)
        except HomeworkModel.DoesNotExist:
            return Response({"error": "Homework not found"}, status=404)

        # Get all assigned students
        assigned_students = homework.assigned_to.all()
        
        submissions_data = []
        for student in assigned_students:
            submission = HomeworkSubmissionModel.objects.filter(
                homework=homework,
                student=student
            ).first()

            if submission:
                submissions_data.append({
                    "student_id": student.id,
                    "student_name": student.student_name,
                    "class": student.student_class,
                    "submitted": True,
                    "submitted_at": submission.submitted_at,
                    "is_late": submission.is_late,
                    "time_taken_minutes": submission.time_taken_minutes,
                    "score": submission.score,
                    "feedback": submission.feedback
                })
            else:
                submissions_data.append({
                    "student_id": student.id,
                    "student_name": student.student_name,
                    "class": student.student_class,
                    "submitted": False,
                    "submitted_at": None,
                    "is_late": None,
                    "time_taken_minutes": None,
                    "score": None,
                    "feedback": None
                })

        # Sort: submitted first, then by score
        submissions_data.sort(key=lambda x: (not x["submitted"], -(x["score"] or 0)))

        submitted_count = sum(1 for s in submissions_data if s["submitted"])

        return Response({
            "homework_info": {
                "id": homework.id,
                "title": homework.title,
                "subject": homework.subject.name if homework.subject else None,
                "due_date": homework.due_date,
                "total_marks": homework.total_marks
            },
            "submissions": submissions_data,
            "total_assigned": len(submissions_data),
            "submitted_count": submitted_count,
            "pending_count": len(submissions_data) - submitted_count
        })

    def put(self, request, submission_id=None):
        """Grade a homework submission"""
        try:
            from user_management.models import HomeworkSubmissionModel
        except ImportError:
            return Response({"error": "Models not yet migrated."}, status=400)

        data = request.data
        
        if not submission_id:
            # Find or create submission
            homework_id = data.get('homework_id')
            student_id = data.get('student_id')
            
            if not homework_id or not student_id:
                return Response({"error": "homework_id and student_id required"}, status=400)
            
            submission, created = HomeworkSubmissionModel.objects.get_or_create(
                homework_id=homework_id,
                student_id=student_id
            )
        else:
            try:
                submission = HomeworkSubmissionModel.objects.get(id=submission_id)
            except HomeworkSubmissionModel.DoesNotExist:
                return Response({"error": "Submission not found"}, status=404)

        if 'score' in data:
            submission.score = data['score']
        if 'feedback' in data:
            submission.feedback = data['feedback']
        if 'submitted_at' in data:
            submission.submitted_at = data['submitted_at']

        submission.save()

        return Response({"message": "Submission graded successfully"})


class TeacherRemarkAPI(APIView):
    """
    Teacher Remarks on students (visible to parents)
    """

    def get(self, request, student_id=None):
        """Get remarks for a student"""
        try:
            from user_management.models import TeacherRemarkModel
        except ImportError:
            return Response({"error": "TeacherRemarkModel not yet migrated."}, status=400)

        if student_id:
            remarks = TeacherRemarkModel.objects.filter(student_id=student_id)
        else:
            # Get remarks created by this teacher
            remarks = TeacherRemarkModel.objects.filter(teacher=request.user)

        remarks = remarks.order_by('-created_at')

        remarks_data = []
        for r in remarks:
            remarks_data.append({
                "id": r.id,
                "student_id": r.student.id,
                "student_name": r.student.student_name,
                "teacher_name": f"{r.teacher.first_name} {r.teacher.last_name}" if r.teacher else None,
                "remark": r.remark,
                "remark_type": r.remark_type,
                "is_visible_to_parent": r.is_visible_to_parent,
                "created_at": r.created_at
            })

        return Response({
            "remarks": remarks_data,
            "total_remarks": len(remarks_data)
        })

    def post(self, request):
        """Create a new remark"""
        try:
            from user_management.models import TeacherRemarkModel
        except ImportError:
            return Response({"error": "TeacherRemarkModel not yet migrated."}, status=400)

        data = request.data

        if 'student_id' not in data or 'remark' not in data:
            return Response({"error": "student_id and remark are required"}, status=400)

        try:
            student = StudentModel.objects.get(id=data['student_id'])
        except StudentModel.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        remark = TeacherRemarkModel.objects.create(
            student=student,
            teacher=request.user,
            remark=data['remark'],
            remark_type=data.get('remark_type', 'general'),
            is_visible_to_parent=data.get('is_visible_to_parent', True)
        )

        return Response({
            "message": "Remark added successfully",
            "remark_id": remark.id
        }, status=201)

    def delete(self, request, remark_id=None):
        """Delete a remark"""
        try:
            from user_management.models import TeacherRemarkModel
        except ImportError:
            return Response({"error": "TeacherRemarkModel not yet migrated."}, status=400)

        if not remark_id:
            remark_id = request.data.get('remark_id')

        try:
            remark = TeacherRemarkModel.objects.get(id=remark_id)
            remark.delete()
            return Response({"message": "Remark deleted successfully"})
        except TeacherRemarkModel.DoesNotExist:
            return Response({"error": "Remark not found"}, status=404)



class HomeAlertsAPI(APIView):
    """
    Home Alerts API - API for home screen alerts
    
    Shows alerts for:
    1. Weak Students     → average score < 60%
    2. Low Engagement    → no study session in last 5 days
    3. Test Not Attempted → no test attempted in last 10 days
    
    """

    def get(self, request, teacher_id):
        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        # --- Get teacher's assigned students ---
        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(
                teacher=teacher, 
                is_active=True
            )
            assigned_classes = teacher_assignment.assigned_classes.all()
            assigned_subjects = teacher_assignment.assigned_subjects.all()
            teacher_role = teacher_assignment.teacher_role or 'subject_teacher'
        except TeacherAssignmentModel.DoesNotExist:
            # Fallback
            students_fallback = StudentModel.objects.filter(
                parent__id=teacher_id
            ).distinct()
            assigned_classes = ClassModel.objects.filter(
                students__in=students_fallback
            ).distinct()
            assigned_subjects = Subject.objects.filter(
                testmodel__created_by=teacher
            ).distinct()
            teacher_role = 'subject_teacher'

        # Get all students from assigned classes
        students = StudentModel.objects.filter(
            student_class__in=assigned_classes
        ).distinct()

        if not students.exists():
            return Response({
                'alerts': [],
                'total_alerts': 0,
                'high_priority': 0,
                'medium_priority': 0,
                'low_priority': 0,
                'message': 'No students found'
            })

        # --- Time references ---
        now = timezone.now()
        five_days_ago = now - timedelta(days=5)
        ten_days_ago = now - timedelta(days=10)

        alerts = []

        for student in students:

            # ============================================
            # CHECK 1 — Weak Student (score < 60%)
            # ============================================
            if teacher_role == 'subject_teacher':
                attempts = StudentTestAttemptModel.objects.filter(
                    student=student,
                    test__subject__in=assigned_subjects
                )
            else:
                attempts = StudentTestAttemptModel.objects.filter(
                    student=student
                )

            if attempts.exists():
                percentages = []
                for attempt in attempts:
                    if attempt.test.total_marks > 0:
                        pct = (attempt.score / attempt.test.total_marks) * 100
                        percentages.append(pct)

                if percentages:
                    avg_score = round(
                        sum(percentages) / len(percentages), 1
                    )

                    if avg_score < 60:
                        # Check if score is dropping (last 3 tests)
                        recent_attempts = attempts.order_by('-started_at')[:3]
                        recent_pcts = []
                        for a in recent_attempts:
                            if a.test.total_marks > 0:
                                recent_pcts.append(
                                    (a.score / a.test.total_marks) * 100
                                )

                        recent_avg = round(
                            sum(recent_pcts) / len(recent_pcts), 1
                        ) if recent_pcts else avg_score

                        # High priority if very low, medium if below 60
                        priority = 'high' if avg_score < 40 else 'medium'

                        alerts.append({
                            'type': 'weak_student',
                            'student_id': student.id,
                            'student_name': student.student_name,
                            'class': student.student_class.get_display_name() if student.student_class else None,
                            'message': f'Average score is {avg_score}%',
                            'detail': f'Recent average: {recent_avg}%',
                            'avg_score': avg_score,
                            'priority': priority,
                            'action': 'View student profile'
                        })

            # ============================================
            # CHECK 2 — Low Engagement (no study in 5 days)
            # ============================================
            last_session = StudySession.objects.filter(
                student=student
            ).order_by('-start_time').first()

            if last_session is None:
                # Never studied at all
                alerts.append({
                    'type': 'low_engagement',
                    'student_id': student.id,
                    'student_name': student.student_name,
                    'class': student.student_class.get_display_name() if student.student_class else None,
                    'message': 'Never opened the app',
                    'detail': 'No study session recorded',
                    'last_active': None,
                    'days_inactive': None,
                    'priority': 'high',
                    'action': 'Contact student'
                })
            elif last_session.start_time < five_days_ago:
                # Calculate how many days inactive
                days_inactive = (now - last_session.start_time).days

                priority = 'high' if days_inactive >= 10 else 'medium'

                alerts.append({
                    'type': 'low_engagement',
                    'student_id': student.id,
                    'student_name': student.student_name,
                    'class': student.student_class.get_display_name() if student.student_class else None,
                    'message': f'Not studied in {days_inactive} days',
                    'detail': f'Last active: {last_session.start_time.strftime("%d %b %Y")}',
                    'last_active': last_session.start_time.date(),
                    'days_inactive': days_inactive,
                    'priority': priority,
                    'action': 'Send reminder'
                })

            # ============================================
            # CHECK 3 — Test Not Attempted (10 days)
            # ============================================
            if teacher_role == 'subject_teacher':
                last_attempt = StudentTestAttemptModel.objects.filter(
                    student=student,
                    test__subject__in=assigned_subjects
                ).order_by('-started_at').first()
            else:
                last_attempt = StudentTestAttemptModel.objects.filter(
                    student=student
                ).order_by('-started_at').first()

            if last_attempt is None:
                # Never attempted any test
                alerts.append({
                    'type': 'test_not_attempted',
                    'student_id': student.id,
                    'student_name': student.student_name,
                    'class': student.student_class.get_display_name() if student.student_class else None,
                    'message': 'Never attempted any test',
                    'detail': 'No test attempt recorded',
                    'last_attempt': None,
                    'days_since_test': None,
                    'priority': 'medium',
                    'action': 'Assign test'
                })
            elif last_attempt.started_at < ten_days_ago:
                days_since_test = (now - last_attempt.started_at).days

                alerts.append({
                    'type': 'test_not_attempted',
                    'student_id': student.id,
                    'student_name': student.student_name,
                    'class': student.student_class.get_display_name() if student.student_class else None,
                    'message': f'No test attempted in {days_since_test} days',
                    'detail': f'Last test: {last_attempt.started_at.strftime("%d %b %Y")}',
                    'last_attempt': last_attempt.started_at.date(),
                    'days_since_test': days_since_test,
                    'priority': 'low',
                    'action': 'Assign test'
                })

        # --- Sort alerts: high first, then medium, then low ---
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))

        # --- Count by priority ---
        high_count = len([a for a in alerts if a['priority'] == 'high'])
        medium_count = len([a for a in alerts if a['priority'] == 'medium'])
        low_count = len([a for a in alerts if a['priority'] == 'low'])

        return Response({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'high_priority': high_count,
            'medium_priority': medium_count,
            'low_priority': low_count,
            'checked_students': students.count(),
            'alert_summary': {
                'weak_students': len([a for a in alerts if a['type'] == 'weak_student']),
                'low_engagement': len([a for a in alerts if a['type'] == 'low_engagement']),
                'test_not_attempted': len([a for a in alerts if a['type'] == 'test_not_attempted']),
            }
        })


class ClassComparisonAPI(APIView):
    """
    Class Comparison API

    Principal:
        - Can see ALL classes

    Teacher:
        - Only assigned classes
        - Only assigned subjects (if subject teacher)
    """

    def get(self, request, user_id):
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # ---------------------------------------------------
        # 1. ROLE CHECK
        # ---------------------------------------------------
        is_principal = user.role.type in ['Admin', 'Principal']

        # ---------------------------------------------------
        # 2. GET CLASSES & SUBJECTS
        # ---------------------------------------------------
        if is_principal:
            assigned_classes = ClassModel.objects.all()
            teacher_role = 'principal'

        else:
            try:
                teacher_assignment = TeacherAssignmentModel.objects.get(
                    teacher=user,
                    is_active=True
                )
                assigned_classes = teacher_assignment.assigned_classes.all()
                teacher_role = teacher_assignment.teacher_role or 'subject_teacher'

            except TeacherAssignmentModel.DoesNotExist:
                assigned_classes = ClassModel.objects.none()
                teacher_role = 'teacher'

        #  ALWAYS TAKE ALL SUBJECTS
        assigned_subjects = Subject.objects.all()

        # Optional subject filter
        subject_id = request.GET.get('subject')

        if subject_id:
            assigned_subjects = assigned_subjects.filter(id=subject_id)

        all_subjects = assigned_subjects

        # ---------------------------------------------------
        # 3. MAIN LOOP (PER CLASS)
        # ---------------------------------------------------
        comparison_data = []

        for class_obj in assigned_classes:

            students = class_obj.students.all()

            if not students.exists():
                continue

            # ---------------------------------------------------
            # 4. ATTEMPTS QUERY (OPTIMIZED)
            # ---------------------------------------------------
            attempts = StudentTestAttemptModel.objects.filter(
                student__in=students,
                test__total_marks__gt=0
            )

            if subject_id:
                attempts = attempts.filter(test__subject_id=subject_id)
                
            attempts = attempts.filter(test__subject__in=assigned_subjects)
            # Add percentage calculation at DB level
            attempts = attempts.annotate(
                percent=F('score') * 100.0 / F('test__total_marks')
            )

            # ---------------------------------------------------
            # 5. SUBJECT-WISE AVERAGE (FIXED COLUMNS)
            # ---------------------------------------------------
            subject_avg_query = attempts.values(
                'test__subject__id',
                'test__subject__name'
            ).annotate(avg=Avg('percent'))

            subject_map = {
                s.id: 0 for s in all_subjects
            }

            for row in subject_avg_query:
                subject_map[row['test__subject__id']] = round(row['avg'], 2)

            subject_avgs = {
                s.name: subject_map.get(s.id, 0)
                for s in all_subjects
            }

            # ---------------------------------------------------
            # 6. CLASS AVERAGE
            # ---------------------------------------------------
            class_avg = attempts.aggregate(avg=Avg('percent'))['avg'] or 0
            class_avg = round(class_avg, 2)

            # ---------------------------------------------------
            # 7. ENGAGEMENT SCORE (LAST 7 DAYS)
            # ---------------------------------------------------
            seven_days_ago = timezone.now() - timedelta(days=7)

            active_students = StudySession.objects.filter(
                student__in=students,
                start_time__gte=seven_days_ago
            ).values('student').distinct().count()

            total_students = students.count()

            engagement = (
                round((active_students / total_students) * 100, 1)
                if total_students > 0 else 0
            )

            # ---------------------------------------------------
            # 8. FINAL OBJECT
            # ---------------------------------------------------
            comparison_data.append({
                'class_id': class_obj.id,
                'class_name': class_obj.get_display_name(),
                'standard': class_obj.standard,
                'section': class_obj.section or '',
                'total_students': total_students,

                # 👇 IMPORTANT FOR TABLE UI
                'subjects': subject_avgs,

                'class_average': class_avg,
                'engagement_score': engagement,
                'active_students': active_students,
                'total_tests': attempts.values('test').distinct().count(),
            })

        # ---------------------------------------------------
        # 9. SORT + RANK
        # ---------------------------------------------------
        comparison_data.sort(
            key=lambda x: x['class_average'],
            reverse=True
        )

        for i, c in enumerate(comparison_data):
            c['rank'] = i + 1

        # ---------------------------------------------------
        # 10. RESPONSE
        # ---------------------------------------------------
        return Response({
            'role': teacher_role,
            'total_classes': len(comparison_data),
            'subjects': [s.name for s in all_subjects],  # 👈 for frontend columns
            'comparison': comparison_data,
            'filter_subject': subject_id or 'All Subjects'
        }, status=status.HTTP_200_OK)
        


class LiveMonitoringAPI(APIView):

    def get(self, request, teacher_id):

        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        # ---------------------------------------------------
        # 1. GET CLASSES + SUBJECTS
        # ---------------------------------------------------
        try:
            ta = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = ta.assigned_classes.all()
            assigned_subjects = ta.assigned_subjects.all()
            teacher_role = ta.teacher_role or 'subject_teacher'
        except TeacherAssignmentModel.DoesNotExist:
            assigned_classes = ClassModel.objects.none()
            assigned_subjects = Subject.objects.none()
            teacher_role = 'subject_teacher'

        students = StudentModel.objects.filter(
            student_class__in=assigned_classes
        ).select_related('student_class').distinct()

        now = timezone.now()
        thirty_min_ago = now - timedelta(minutes=30)

        local_now = localtime(now)
        today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
       
        
        local_now = localtime(now)

        today_start = local_now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # ---------------------------------------------------
        # 2. BULK FETCH SESSIONS (OPTIMIZED)
        # ---------------------------------------------------
        sessions = StudySession.objects.filter(
            student__in=students
        ).select_related('subject', 'student')

        live_sessions = sessions.filter(
            start_time__gte=thirty_min_ago,
            end_time__isnull=True
        )

        today_sessions = sessions.filter(
            start_time__gte=today_start
        )

        # Group sessions by student
        from collections import defaultdict

        live_map = {}
        today_map = defaultdict(list)
        last_session_map = {}

        for s in sessions.order_by('-start_time'):
            sid = s.student_id

            if sid not in last_session_map:
                last_session_map[sid] = s

            today_date = timezone.localdate()

            if timezone.localtime(s.start_time).date() == today_date:
                today_map[sid].append(s)
                
            if s.end_time is None:
                if sid not in live_map:
                    live_map[sid] = s

        # ---------------------------------------------------
        # 3. BUILD RESPONSE
        # ---------------------------------------------------
        active_now = []
        studying_today = []
        inactive = []

        assigned_subject_ids = set(assigned_subjects.values_list('id', flat=True))

        for student in students:

            sid = student.id

            live_session = live_map.get(sid)
            today_student_sessions = today_map.get(sid, [])
            last_session = last_session_map.get(sid)

            # ✅ REPLACE HERE
            total_seconds = 0

            for s in today_student_sessions:
                if s.end_time:
                    total_seconds += (s.end_time - s.start_time).total_seconds()
                else:
                    total_seconds += (now - s.start_time).total_seconds()

            today_minutes = round(total_seconds / 60, 1)

            student_info = {
                'student_id': sid,
                'student_name': student.student_name,
                'class': student.student_class.get_display_name() if student.student_class else None,
                'today_study_minutes': today_minutes,
                'last_seen': timezone.localtime(last_session.start_time).strftime('%H:%M') if last_session else None,
            }

            # ---------------------------------------------------
            # LIVE
            # ---------------------------------------------------
            if live_session:
                if teacher_role == 'subject_teacher' and live_session.subject_id not in assigned_subject_ids:
                    continue

                duration_so_far = round(
                    (now - live_session.start_time).total_seconds() / 60,
                    1
                )

                active_now.append({
                    **student_info,
                    'current_subject': live_session.subject.name if live_session.subject else 'Unknown',
                    'session_started': timezone.localtime(live_session.start_time).strftime('%H:%M'),
                    'duration_minutes': duration_so_far,
                    'status': 'live'
                })

            # ---------------------------------------------------
            # STUDIED TODAY
            # ---------------------------------------------------
            elif today_student_sessions:
                studying_today.append({
                    **student_info,
                    'status': 'studied_today'
                })

            # ---------------------------------------------------
            # INACTIVE
            # ---------------------------------------------------
            else:
                inactive.append({
                    **student_info,
                    'status': 'not_active'
                })

        # ---------------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------------
        return Response({
            'live_count': len(active_now),
            'studied_today_count': len(studying_today),
            'inactive_count': len(inactive),
            'total_students': students.count(),
            'last_updated': timezone.localtime(now).strftime('%H:%M:%S'),
            'active_now': active_now,
            'studied_today': studying_today,
            'inactive': inactive,
        })
        
class ReportsAPI(APIView):
    """
    Generate class or student summary reports
    """
    def get(self, request, teacher_id):
        report_type = request.GET.get('report_type', 'class')  # 'class' or 'student'
        class_id = request.GET.get('class_id')
        student_id = request.GET.get('student_id')
        subject_id = request.GET.get('subject')
        date_range = int(request.GET.get('date_range', 30))

        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        try:
            teacher_assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = teacher_assignment.assigned_classes.all()
            assigned_subjects = teacher_assignment.assigned_subjects.all()
            teacher_role = teacher_assignment.teacher_role or 'subject_teacher'
        except TeacherAssignmentModel.DoesNotExist:
            students_fb = StudentModel.objects.filter(parent__id=teacher_id).distinct()
            assigned_classes = ClassModel.objects.filter(students__in=students_fb).distinct()
            assigned_subjects = Subject.objects.filter(testmodel__created_by=teacher).distinct()
            teacher_role = 'subject_teacher'

        start = timezone.now() - timedelta(days=date_range)

        if report_type == 'student' and student_id:
            try:
                student = StudentModel.objects.get(id=student_id)
            except StudentModel.DoesNotExist:
                return Response({'error': 'Student not found'}, status=404)

            attempts = StudentTestAttemptModel.objects.filter(
                student=student, started_at__gte=start
            )
            if subject_id:
                attempts = attempts.filter(test__subject_id=subject_id)
            elif teacher_role == 'subject_teacher':
                attempts = attempts.filter(test__subject__in=assigned_subjects)

            sessions = StudySession.objects.filter(student=student, start_time__gte=start)
            total_study = sum(s.duration or 0 for s in sessions)

            percentages = []
            test_report = []
            for attempt in attempts.order_by('started_at'):
                if attempt.test.total_marks > 0:
                    pct = round((attempt.score / attempt.test.total_marks) * 100, 2)
                    percentages.append(pct)
                    test_report.append({
                        'test_title': attempt.test.title,
                        'subject': attempt.test.subject.name if attempt.test.subject else 'Unknown',
                        'score': attempt.score,
                        'total_marks': attempt.test.total_marks,
                        'percentage': pct,
                        'date': attempt.started_at.date(),
                    })

            avg = round(sum(percentages) / len(percentages), 2) if percentages else 0

            return Response({
                'report_type': 'student',
                'student_name': student.student_name,
                'class': student.student_class.get_display_name() if student.student_class else None,
                'date_range': f'Last {date_range} days',
                'summary': {
                    'total_tests': len(test_report),
                    'average_score': avg,
                    'total_study_minutes': round(total_study / 60, 1),
                    'total_sessions': sessions.count(),
                    'performance_tag': 'Strong' if avg >= 75 else 'Average' if avg >= 50 else 'Weak',
                },
                'test_history': test_report,
            })

        # Default: class report
        if class_id:
            try:
                class_obj = ClassModel.objects.get(id=class_id)
            except ClassModel.DoesNotExist:
                return Response({'error': 'Class not found'}, status=404)
            classes = [class_obj]
        else:
            classes = assigned_classes

        class_reports = []
        for class_obj in classes:
            students = class_obj.students.all()
            attempts = StudentTestAttemptModel.objects.filter(
                student__in=students, started_at__gte=start
            )
            if subject_id:
                attempts = attempts.filter(test__subject_id=subject_id)
            elif teacher_role == 'subject_teacher':
                attempts = attempts.filter(test__subject__in=assigned_subjects)

            percentages = []
            for a in attempts:
                if a.test.total_marks > 0:
                    percentages.append((a.score / a.test.total_marks) * 100)
            class_avg = round(sum(percentages) / len(percentages), 2) if percentages else 0

            # Per-student summary
            student_summaries = []
            for student in students:
                s_attempts = attempts.filter(student=student)
                s_pcts = []
                for a in s_attempts:
                    if a.test.total_marks > 0:
                        s_pcts.append((a.score / a.test.total_marks) * 100)
                s_avg = round(sum(s_pcts) / len(s_pcts), 2) if s_pcts else 0
                student_summaries.append({
                    'student_id': student.id,
                    'student_name': student.student_name,
                    'average_score': s_avg,
                    'tests_taken': len(s_pcts),
                    'status': get_student_status(student),
                    'last_activity': get_last_activity(student),
                })

            student_summaries.sort(key=lambda x: -x['average_score'])

            class_reports.append({
                'class_id': class_obj.id,
                'class_name': class_obj.get_display_name(),
                'total_students': students.count(),
                'class_average': class_avg,
                'total_tests': attempts.values('test').distinct().count(),
                'student_summaries': student_summaries,
            })

        return Response({
            'report_type': 'class',
            'date_range': f'Last {date_range} days',
            'generated_at': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'class_reports': class_reports,
        })

class TeacherSettingsAPI(APIView):
    """
    View and update teacher profile & notification preferences
    """
    def get(self, request, teacher_id):
        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        try:
            assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            assigned_classes = [{'id': c.id, 'name': c.get_display_name()} for c in assignment.assigned_classes.all()]
            assigned_subjects = [{'id': s.id, 'name': s.name} for s in assignment.assigned_subjects.all()]
            teacher_role = assignment.teacher_role or 'subject_teacher'
            homeroom = {'id': assignment.homeroom_class.id, 'name': assignment.homeroom_class.get_display_name()} if assignment.homeroom_class else None
        except TeacherAssignmentModel.DoesNotExist:
            assigned_classes = []
            assigned_subjects = []
            teacher_role = 'subject_teacher'
            homeroom = None

        return Response({
            'profile': {
                'id': teacher.id,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'email': teacher.email,
                'role': teacher_role,
            },
            'assignment': {
                'assigned_classes': assigned_classes,
                'assigned_subjects': assigned_subjects,
                'homeroom_class': homeroom,
            },
            'notifications': {
                'weak_student_alerts': True,
                'low_engagement_alerts': True,
                'test_submission_alerts': True,
            }
        })

    def patch(self, request, teacher_id):
        try:
            teacher = UserModel.objects.get(id=teacher_id, role__type='Teacher')
        except UserModel.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=404)

        data = request.data

        if 'first_name' in data:
            teacher.first_name = data['first_name']
        if 'last_name' in data:
            teacher.last_name = data['last_name']
        if 'email' in data:
            teacher.email = data['email']

        teacher.save()

        try:
            assignment = TeacherAssignmentModel.objects.get(teacher=teacher, is_active=True)
            if 'weak_student_alerts' in data:
                assignment.notif_weak_student = data['weak_student_alerts']
            if 'low_engagement_alerts' in data:
                assignment.notif_low_engagement = data['low_engagement_alerts']
            if 'test_submission_alerts' in data:
                assignment.notif_test_submission = data['test_submission_alerts']
            assignment.save()
        except TeacherAssignmentModel.DoesNotExist:
            pass
 
        return Response({'message': 'Settings updated successfully'})


class CreateHomeworkView(APIView):
    """
    POST /api/homework/create/
    Create homework and optionally assign to a group in one call.
 
    Body:
    {
        "title": "Chapter 5 Problems",
        "subject_id": 2,
        "description": "Solve exercises 1-10",
        "due_date": "2026-05-20T18:00:00Z",
        "total_marks": 50,
        "group_id": 3          ← optional, assigns to all students in group
    }
    """
    def post(self, request):
        serializer = HomeworkCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            homework = serializer.save()
            return Response({
                'message': 'Homework created successfully',
                'homework_id': homework.id,
                'assigned_students': homework.assigned_to.count()
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
class AssignHomeworkToGroupView(APIView):
    """
    POST /api/homework/<homework_id>/assign-group/
    Assign an EXISTING homework to a group.
    Body: { "group_id": 3 }
    """
    def post(self, request, homework_id):
        try:
            homework = HomeworkModel.objects.get(id=homework_id)
        except HomeworkModel.DoesNotExist:
            return Response(
                {'error': 'Homework not found'},
                status=status.HTTP_404_NOT_FOUND
            )
 
        serializer = HomeworkAssignToGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(homework=homework)
            group = serializer.validated_data['group_id']
            return Response({
                'message': f'Homework assigned to group "{group.name}"',
                'homework_id': homework.id,
                'group_id': group.id,
                'group_name': group.name,
                'total_assigned': homework.assigned_to.count()
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
class GroupHomeworkListView(APIView):
    """
    GET /api/groups/<group_id>/homework/
    List all homework assigned to a group.
    """
    def get(self, request, group_id):
        try:
            group = StudentGroupModel.objects.get(id=group_id)
        except StudentGroupModel.DoesNotExist:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND
            )
 
        homework_list = HomeworkModel.objects.filter(group=group).select_related('subject')
        serializer = HomeworkDetailSerializer(homework_list, many=True)
        return Response({
            'group_id': group_id,
            'group_name': group.name,
            'homework': serializer.data
        })
 
 
# ------------------------------------------------------------
# B) SUGGESTED TESTS FOR GROUP  (real recommendation logic)
# ------------------------------------------------------------
 
class GroupSuggestedTestsView(APIView):
    # """
    # GET /api/groups/<group_id>/suggested-tests/
    # Returns AI-recommended tests for the group based on:
    # - Subjects where group avg score < 60%  → HIGH priority
    # - Tests not yet attempted by group      → MEDIUM priority
    # """
    # def get(self, request, group_id):
    #     result = SuggestedTestSerializer.get_suggestions(group_id)
    #     if result is None:
    #         return Response(
    #             {'error': 'Group not found'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )
    #     return Response(result, status=status.HTTP_200_OK)
    """
    GET /api/groups/<group_id>/suggested-tests/
 
    Recommendation logic:
      HIGH priority   → subject where group avg score < 60%
      MEDIUM priority → tests not yet attempted by ≥50% of the group
    """
 
    def get(self, request, group_id):
        try:
            group = StudentGroupModel.objects.prefetch_related('students').get(
                id=group_id
            )
        except StudentGroupModel.DoesNotExist:
            return Response({'error': 'Group not found'},
                            status=status.HTTP_404_NOT_FOUND)
 
        student_ids = list(group.students.values_list('id', flat=True))
        if not student_ids:
            return Response({
                'group_id':   group_id,
                'group_name': group.name,
                'suggestions': [],
                'reason':     'No students in group',
            })
 
        # ── 1. Weak subjects (avg score < 60%) ──────────────────────────────
        attempts_qs = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids,
            test__total_marks__gt=0,
        ).annotate(
            pct=F('score') * 100.0 / F('test__total_marks')
        )
 
        subject_stats = (
            attempts_qs
            .values('test__subject__id', 'test__subject__name')
            .annotate(avg_score=Avg('pct'), attempt_count=Count('id'))
        )
 
        weak_subject_ids = [
            row['test__subject__id']
            for row in subject_stats
            if row['avg_score'] is not None and row['avg_score'] < 60
        ]
 
        weak_subject_avg = {
            row['test__subject__id']: round(row['avg_score'], 1)
            for row in subject_stats
            if row['avg_score'] is not None and row['avg_score'] < 60
        }
 
        # ── 2. Tests already done by > 50% of group ─────────────────────────
        already_attempted = (
            StudentTestAttemptModel.objects
            .filter(student_id__in=student_ids)
            .values('test_id')
            .annotate(attempt_count=Count('student_id', distinct=True))
            .filter(attempt_count__gte=len(student_ids) * 0.5)
            .values_list('test_id', flat=True)
        )
 
        # ── 3. Build recommendations ─────────────────────────────────────────
        recommended = (
            TestModel.objects
            .filter(
                Q(subject_id__in=weak_subject_ids) |
                Q(subject__isnull=False)
            )
            .exclude(id__in=already_attempted)
            .select_related('subject')
            .distinct()[:15]
        )
 
        suggestions = []
        for test in recommended:
            is_weak_subject = test.subject_id in weak_subject_ids
            if is_weak_subject:
                avg = weak_subject_avg.get(test.subject_id, 0)
                reason   = (
                    f'Group is weak in {test.subject.name} '
                    f'(avg {avg}% < 60%)'
                )
                priority = 'high'
            else:
                reason   = 'Not yet attempted by most group members'
                priority = 'medium'
 
            # Per-student attempt count for this test
            attempted_count = StudentTestAttemptModel.objects.filter(
                test=test, student_id__in=student_ids
            ).values('student_id').distinct().count()
 
            suggestions.append({
                'test_id':        test.id,
                'title':          test.title,
                'subject':        test.subject.name if test.subject else None,
                'total_marks':    test.total_marks,
                'questions':      test.number_of_questions,
                'question_type':  test.question_type,
                'reason':         reason,
                'priority':       priority,
                'attempted_by':   attempted_count,
                'total_students': len(student_ids),
                'attempt_rate':   round(
                    attempted_count / len(student_ids) * 100, 1
                ),
            })
 
        # Sort: high first, then medium; within same priority sort by attempt_rate asc
        suggestions.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1,
            x['attempt_rate'],
        ))
 
        return Response({
            'group_id':     group.id,
            'group_name':   group.name,
            'student_count': len(student_ids),
            'weak_subjects': [
                {'id': sid, 'avg': avg}
                for sid, avg in weak_subject_avg.items()
            ],
            'suggestions':  suggestions,
        }, status=status.HTTP_200_OK)
 

class NotificationPreferenceView(APIView):
    """
    GET  /api/notifications/preferences/?user_id=5
         /api/notifications/preferences/?student_id=3
 
    POST /api/notifications/preferences/
    {
        "user_id": 5,
        "homework_assigned": true,
        "test_scheduled": false,
        "push_enabled": true
    }
 
    PATCH /api/notifications/preferences/
    {
        "user_id": 5,
        "push_enabled": false,
        "weekly_report": true
    }
    FIXED: PATCH was not actually persisting preference field changes.
    """
 
    PREF_FIELDS = [
        'homework_assigned', 'homework_due', 'homework_graded',
        'test_scheduled', 'test_result',
        'goal_achieved', 'badge_earned', 'weekly_report',
        'teacher_remark',
        'push_enabled', 'email_enabled', 'sms_enabled',
    ]
 
    def _resolve_owner(self, data):
        """
        Returns (filter_kwargs, error_message).
        Accepts both dict (request.data) and QueryDict (request.query_params).
        """
        user_id    = data.get('user_id')
        student_id = data.get('student_id')
 
        if not user_id and not student_id:
            return None, 'Provide either user_id or student_id'
 
        if user_id:
            try:
                owner = UserModel.objects.get(id=user_id)
                return {'user': owner}, None
            except UserModel.DoesNotExist:
                return None, 'User not found'
 
        try:
            owner = StudentModel.objects.get(id=student_id)
            return {'student': owner}, None
        except StudentModel.DoesNotExist:
            return None, 'Student not found'
 
    def get(self, request):
        filter_kwargs, error = self._resolve_owner(request.query_params)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
 
        pref, _ = NotificationPreferenceModel.objects.get_or_create(**filter_kwargs)
        return Response(NotificationPreferenceSerializer(pref).data)
 
    def post(self, request):
        filter_kwargs, error = self._resolve_owner(request.data)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
 
        pref, created = NotificationPreferenceModel.objects.get_or_create(**filter_kwargs)
        serializer = NotificationPreferenceSerializer(
            pref, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message':     'Preferences saved',
                'created':     created,
                'preferences': serializer.data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def patch(self, request):
        """
        FIXED: This was missing entirely. PATCH now finds the preference record
        and updates only the fields provided, then saves to DB.
        """
        filter_kwargs, error = self._resolve_owner(request.data)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
 
        try:
            pref = NotificationPreferenceModel.objects.get(**filter_kwargs)
        except NotificationPreferenceModel.DoesNotExist:
            # Auto-create with defaults if not found
            pref = NotificationPreferenceModel.objects.create(**filter_kwargs)
 
        # Apply only the preference fields present in the request
        updated_fields = []
        for field in self.PREF_FIELDS:
            if field in request.data:
                value = request.data[field]
                # Accept both bool and string ('true'/'false') from form data
                if isinstance(value, str):
                    value = value.lower() == 'true'
                setattr(pref, field, value)
                updated_fields.append(field)
 
        if not updated_fields:
            return Response(
                {'error': f'No preference fields found. Valid fields: {self.PREF_FIELDS}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        pref.save(update_fields=updated_fields + ['updated_at'])
 
        return Response({
            'message':         'Preferences updated',
            'updated_fields':  updated_fields,
            'preferences':     NotificationPreferenceSerializer(pref).data,
        }, status=status.HTTP_200_OK)
 
