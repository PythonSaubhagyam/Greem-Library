# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication

# from user_management.models import *
# from adminpanel.utils.analytics import *
# from django.db.models import Avg

# class PrincipalFlowAPI(APIView):
#     authentication_classes = [SessionAuthentication, BasicAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         principal_id = request.query_params.get('principal_id')
#         if not principal_id:
#             return Response({"error": "principal_id is required"}, status=400)

#         today = timezone.now().date()
#         one_week_ago = timezone.now() - timedelta(days=7)

#         # ---- Build the scoped hierarchy for this principal ----
#         coordinators_mapping = PrincipalCoordinatorMapping.objects.filter(principal_id=principal_id)
#         coordinator_ids = list(coordinators_mapping.values_list('coordinator_id', flat=True))
#         total_coordinators = len(coordinator_ids)

#         teacher_mappings = CoordinatorTeacherMapping.objects.filter(coordinator_id__in=coordinator_ids)
#         teacher_ids = list(teacher_mappings.values_list('teacher_id', flat=True).distinct())

#         teachers_qs = UserModel.objects.filter(id__in=teacher_ids, role__type='Teacher')
#         total_teachers = teachers_qs.count()

#         assignments = TeacherAssignmentModel.objects.filter(teacher_id__in=teacher_ids)
#         class_ids = set()
#         for a in assignments:
#             class_ids.update(a.assigned_classes.values_list('id', flat=True))

#         classes_qs = ClassModel.objects.filter(id__in=class_ids)
#         total_classes = classes_qs.count()

#         students_qs = StudentModel.objects.filter(student_class_id__in=class_ids)
#         total_students = students_qs.count()

#         # ---- Now every metric below uses the scoped querysets ----
#         active_students_today = StudySession.objects.filter(
#             start_time__date=today, student__in=students_qs
#         ).values('student').distinct().count()

#         active_teachers_today = UserModel.objects.filter(
#             Q(id__in=teacher_ids) &
#             (Q(testmodel__created_at__date=today) | Q(created_homework__created_at__date=today))
#         ).distinct().count()

#         sls_scores = [calculate_student_learning_score(s.id) for s in students_qs]
#         weak_students_count = len([s for s in sls_scores if s < 40])

#         class_scores = [calculate_class_health_score(c.id) for c in classes_qs]
#         weak_classes_count = len([c for c in class_scores if c < 40])

#         pending_homework = HomeworkSubmissionModel.objects.filter(
#             submitted_at__isnull=True, student__in=students_qs
#         ).count()

#         tests_this_week = TestModel.objects.filter(
#             created_at__gte=one_week_ago, created_by__in=teacher_ids
#         ).count()

#         study_minutes_today = StudySession.objects.filter(
#             start_time__date=today, student__in=students_qs
#         ).aggregate(total=Sum('duration'))['total'] or 0
#         study_hours_today = round(study_minutes_today / 60, 1)

#         avg_teacher_activity = (
#             sum(calculate_teacher_accountability_score(t.id) for t in teachers_qs) / total_teachers
#             if total_teachers > 0 else 0
#         )
#         avg_coordinator_activity = (
#             sum(calculate_coordinator_control_score(c.coordinator_id) for c in coordinators_mapping) / total_coordinators
#             if total_coordinators > 0 else 0
#         )

#         action_required_count = weak_students_count + weak_classes_count + (1 if pending_homework > 50 else 0)

#         data = {
#             "school_overview": {
#                 "total_students": total_students,
#                 "active_students_today": active_students_today,
#                 "total_teachers": total_teachers,
#                 "active_teachers_today": active_teachers_today,
#                 "total_classes": total_classes,
#                 "weak_students": weak_students_count,
#                 "weak_classes": weak_classes_count,
#                 "pending_homework": pending_homework,
#                 "tests_this_week": tests_this_week,
#                 "study_hours_today": study_hours_today,
#                 "teacher_activity_score": round(avg_teacher_activity, 2),
#                 "coordinator_activity_score": round(avg_coordinator_activity, 2),
#                 "device_usage": {
#                     "active": active_students_today,
#                     "inactive": total_students - active_students_today,
#                     "issues": 0,
#                 },
#                 "action_required_count": action_required_count,
#             },
#             "coordinators": [
#                 {
#                     "id": c.coordinator.id,
#                     "name": f"{c.coordinator.first_name} {c.coordinator.last_name}",
#                     "control_score": calculate_coordinator_control_score(c.coordinator.id)
#                 } for c in coordinators_mapping
#             ]
#         }
#         return Response(data)
       

# class PrincipalModuleAPI(APIView):
#     """
#     Unified API for the 15 Modules defined in Section 2 of the Specification.
#     Each module returns its 'Core Objective' data.
#     """
#     def get(self, request, module_name):
#         if module_name == 'students':
#             # Section 5: Student Performance Intelligence
#             all_students = StudentModel.objects.all()
#             data = [{
#                 "id": s.id,
#                 "name": s.student_name,
#                 "learning_score": calculate_student_learning_score(s.id),
#                 "risk_tag": "High Risk" if calculate_student_learning_score(s.id) < 40 else "Stable",
#                 "homework_pct": "85%", # Placeholder
#                 "improvement": "+5%" # Placeholder
#             } for s in all_students]
#             return Response({"module": "Students", "data": data})

#         elif module_name == 'classes':
#             # Section 6: Class Performance Dashboard
#             all_classes = ClassModel.objects.all()
#             data = [{
#                 "id": c.id,
#                 "name": c.get_display_name(),
#                 "health_score": calculate_class_health_score(c.id),
#                 "weak_students_pct": "15%", # Placeholder
#                 "homework_completion": "92%" # Placeholder
#             } for c in all_classes]
#             return Response({"module": "Classes", "data": data})

#         elif module_name == 'teachers':
#             # Section 7: Teacher Performance Analytics
#             teachers = UserModel.objects.filter(role__type='Teacher')
#             data = [{
#                 "id": t.id,
#                 "name": f"{t.first_name} {t.last_name}",
#                 "accountability_score": calculate_teacher_accountability_score(t.id),
#                 "active_today": "Yes", # Placeholder
#                 "tests_taken": 12 # Placeholder
#             } for t in teachers]
#             return Response({"module": "Teachers", "data": data})

#         return Response({"error": "Module not found or not yet implemented"}, status=404)

# class CoordinatorDetailAPI(APIView):
#     def get(self, request, coordinator_id):
#         teachers = CoordinatorTeacherMapping.objects.filter(coordinator_id=coordinator_id)
        
#         data = {
#             "coordinator_id": coordinator_id,
#             "control_score": calculate_coordinator_control_score(coordinator_id),
#             "teachers": [
#                 {
#                     "id": t.teacher.id,
#                     "name": f"{t.teacher.first_name} {t.teacher.last_name}",
#                     "accountability_score": calculate_teacher_accountability_score(t.teacher.id),
#                     "classes": [c.get_display_name() for c in t.assigned_classes.all()]
#                 } for t in teachers
#             ]
#         }
#         return Response(data)

# class TeacherDetailAPI(APIView):
#     def get(self, request, teacher_id):
#         assignment = TeacherAssignmentModel.objects.filter(teacher_id=teacher_id).first()
#         if not assignment:
#             return Response({"error": "Teacher assignment not found"}, status=404)

#         data = {
#             "teacher_id": teacher_id,
#             "accountability_score": calculate_teacher_accountability_score(teacher_id),
#             "classes": [
#                 {
#                     "id": c.id,
#                     "name": c.get_display_name(),
#                     "health_score": calculate_class_health_score(c.id),
#                     "student_count": c.student_count()
#                 } for c in assignment.assigned_classes.all()
#             ]
#         }
#         return Response(data)

# class ClassDetailAPI(APIView):
#     def get(self, request, class_id):
#         students = StudentModel.objects.filter(student_class_id=class_id)
        
#         data = {
#             "class_id": class_id,
#             "health_score": calculate_class_health_score(class_id),
#             "students": [
#                 {
#                     "id": s.id,
#                     "name": s.student_name,
#                     "learning_score": calculate_student_learning_score(s.id),
#                     "risk_level": "High" if calculate_student_learning_score(s.id) < 40 else "Stable"
#                 } for s in students
#             ]
#         }
#         return Response(data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from user_management.models import *
from adminpanel.utils.analytics import *
from django.db.models import Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta


def get_principal_scope(principal_id):
    """
    Returns the full scoped hierarchy (querysets/ids) for a given principal.
    Reused by every endpoint so 'school-wise' scoping stays consistent everywhere.
    """
    coordinators_mapping = PrincipalCoordinatorMapping.objects.filter(principal_id=principal_id)
    coordinator_ids = list(coordinators_mapping.values_list('coordinator_id', flat=True))

    teacher_mappings = CoordinatorTeacherMapping.objects.filter(coordinator_id__in=coordinator_ids)
    teacher_ids = list(teacher_mappings.values_list('teacher_id', flat=True).distinct())

    assignments = TeacherAssignmentModel.objects.filter(teacher_id__in=teacher_ids)
    class_ids = set()
    for a in assignments:
        class_ids.update(a.assigned_classes.values_list('id', flat=True))

    students_qs = StudentModel.objects.filter(student_class_id__in=class_ids)
    students_qs = StudentModel.objects.filter(parent__id=principal_id).distinct()

    return {
        "coordinators_mapping": coordinators_mapping,
        "coordinator_ids": coordinator_ids,
        "teacher_ids": teacher_ids,
        "class_ids": class_ids,
        "students_qs": students_qs,
    }


class PrincipalFlowAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        principal_id = request.query_params.get('principal_id')
        if not principal_id:
            return Response({"error": "principal_id is required"}, status=400)

        today = timezone.now().date()
        one_week_ago = timezone.now() - timedelta(days=7)

        scope = get_principal_scope(principal_id)
        coordinators_mapping = scope["coordinators_mapping"]
        coordinator_ids = scope["coordinator_ids"]
        teacher_ids = scope["teacher_ids"]
        class_ids = scope["class_ids"]
        students_qs = scope["students_qs"]

        total_coordinators = len(coordinator_ids)

        teachers_qs = UserModel.objects.filter(id__in=teacher_ids, role__type='Teacher')
        total_teachers = teachers_qs.count()

        classes_qs = ClassModel.objects.filter(id__in=class_ids)
        total_classes = classes_qs.count()

        total_students = students_qs.count()

        active_students_today = StudySession.objects.filter(
            start_time__date=today, student__in=students_qs
        ).values('student').distinct().count()

        active_teachers_today = UserModel.objects.filter(
            Q(id__in=teacher_ids) &
            (Q(testmodel__created_at__date=today) | Q(created_homework__created_at__date=today))
        ).distinct().count()

        sls_scores = [calculate_student_learning_score(s.id) for s in students_qs]
        weak_students_count = len([s for s in sls_scores if s < 40])

        class_scores = [calculate_class_health_score(c.id) for c in classes_qs]
        weak_classes_count = len([c for c in class_scores if c < 40])

        pending_homework = HomeworkSubmissionModel.objects.filter(
            submitted_at__isnull=True, student__in=students_qs
        ).count()

        tests_this_week = TestModel.objects.filter(
            created_at__gte=one_week_ago, created_by__in=teacher_ids
        ).count()

        study_minutes_today = StudySession.objects.filter(
            start_time__date=today, student__in=students_qs
        ).aggregate(total=Sum('duration'))['total'] or 0
        study_hours_today = round(study_minutes_today / 60, 1)

        avg_teacher_activity = (
            sum(calculate_teacher_accountability_score(t.id) for t in teachers_qs) / total_teachers
            if total_teachers > 0 else 0
        )
        avg_coordinator_activity = (
            sum(calculate_coordinator_control_score(c.coordinator_id) for c in coordinators_mapping) / total_coordinators
            if total_coordinators > 0 else 0
        )

        action_required_count = weak_students_count + weak_classes_count + (1 if pending_homework > 50 else 0)

        data = {
            "school_overview": {
                "total_students": total_students,
                "active_students_today": active_students_today,
                "total_teachers": total_teachers,
                "active_teachers_today": active_teachers_today,
                "total_classes": total_classes,
                "total_coordinators": total_coordinators,
                "weak_students": weak_students_count,
                "weak_classes": weak_classes_count,
                "pending_homework": pending_homework,
                "tests_this_week": tests_this_week,
                "study_hours_today": study_hours_today,
                "teacher_activity_score": round(avg_teacher_activity, 2),
                "coordinator_activity_score": round(avg_coordinator_activity, 2),
                "health_score": round(sum(sls_scores) / len(sls_scores), 2) if sls_scores else 0,
                "device_usage": {
                    "active": active_students_today,
                    "inactive": total_students - active_students_today,
                    "issues": 0,
                },
                "action_required_count": action_required_count,
            },
            "coordinators": [
                {
                    "id": c.coordinator.id,
                    "name": f"{c.coordinator.first_name} {c.coordinator.last_name}",
                    "control_score": calculate_coordinator_control_score(c.coordinator.id)
                } for c in coordinators_mapping
            ]
        }
        return Response(data)


class CoordinatorDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, coordinator_id):
        principal_id = request.user.id  # principal is whoever is logged in

        # ── School-wise check: this coordinator must belong to this principal ──
        if not PrincipalCoordinatorMapping.objects.filter(
            principal_id=principal_id, coordinator_id=coordinator_id
        ).exists():
            return Response({"error": "Coordinator not found in your school"}, status=404)

        teachers = CoordinatorTeacherMapping.objects.filter(coordinator_id=coordinator_id)

        data = {
            "coordinator_id": coordinator_id,
            "control_score": calculate_coordinator_control_score(coordinator_id),
            "teachers": [
                {
                    "id": t.teacher.id,
                    "name": f"{t.teacher.first_name} {t.teacher.last_name}",
                    "accountability_score": calculate_teacher_accountability_score(t.teacher.id),
                    "classes": [c.get_display_name() for c in t.assigned_classes.all()]
                } for t in teachers
            ]
        }
        return Response(data)


class TeacherDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, teacher_id):
        principal_id = request.user.id
        scope = get_principal_scope(principal_id)

        # ── School-wise check: this teacher must be under one of this principal's coordinators ──
        if teacher_id not in scope["teacher_ids"]:
            return Response({"error": "Teacher not found in your school"}, status=404)

        assignment = TeacherAssignmentModel.objects.filter(teacher_id=teacher_id).first()
        if not assignment:
            return Response({"error": "Teacher assignment not found"}, status=404)

        data = {
            "teacher_id": teacher_id,
            "accountability_score": calculate_teacher_accountability_score(teacher_id),
            "classes": [
                {
                    "id": c.id,
                    "name": c.get_display_name(),
                    "health_score": calculate_class_health_score(c.id),
                    "student_count": c.student_count()
                } for c in assignment.assigned_classes.all()
            ]
        }
        return Response(data)


class ClassDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, class_id):
        principal_id = request.user.id
        scope = get_principal_scope(principal_id)

        # ── School-wise check: this class must be in this principal's school ──
        if class_id not in scope["class_ids"]:
            return Response({"error": "Class not found in your school"}, status=404)

        students = StudentModel.objects.filter(student_class_id=class_id)

        data = {
            "class_id": class_id,
            "health_score": calculate_class_health_score(class_id),
            "students": [
                {
                    "id": s.id,
                    "name": s.student_name,
                    "learning_score": calculate_student_learning_score(s.id),
                    "risk_level": "High" if calculate_student_learning_score(s.id) < 40 else "Stable"
                } for s in students
            ]
        }
        return Response(data)


class PrincipalModuleAPI(APIView):
    """
    Unified API for the 15 Modules defined in Section 2 of the Specification.
    Now school-wise scoped instead of returning all-school data.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, module_name):
        principal_id = request.user.id
        scope = get_principal_scope(principal_id)

        if module_name == 'students':
            students = scope["students_qs"]
            data = [{
                "id": s.id,
                "name": s.student_name,
                "learning_score": calculate_student_learning_score(s.id),
                "risk_tag": "High Risk" if calculate_student_learning_score(s.id) < 40 else "Stable",
                "homework_pct": "85%",  # Placeholder
                "improvement": "+5%"    # Placeholder
            } for s in students]
            return Response({"module": "Students", "data": data})

        elif module_name == 'classes':
            classes = ClassModel.objects.filter(id__in=scope["class_ids"])
            data = [{
                "id": c.id,
                "name": c.get_display_name(),
                "health_score": calculate_class_health_score(c.id),
                "weak_students_pct": "15%",       # Placeholder
                "homework_completion": "92%"      # Placeholder
            } for c in classes]
            return Response({"module": "Classes", "data": data})

        elif module_name == 'teachers':
            teachers = UserModel.objects.filter(id__in=scope["teacher_ids"], role__type='Teacher')
            data = [{
                "id": t.id,
                "name": f"{t.first_name} {t.last_name}",
                "accountability_score": calculate_teacher_accountability_score(t.id),
                "active_today": "Yes",  # Placeholder
                "tests_taken": 12       # Placeholder
            } for t in teachers]
            return Response({"module": "Teachers", "data": data})

        return Response({"error": "Module not found or not yet implemented"}, status=404)

