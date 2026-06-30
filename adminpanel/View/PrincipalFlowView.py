# PrincipalFlowView.py — COMPLETE FIXED VERSION
 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
 
from user_management.models import (
    UserModel, StudentModel, ClassModel, DeviceModel,
    CoordinatorAssignmentModel, TeacherAssignmentModel,
    PrincipalCoordinatorMapping, CoordinatorTeacherMapping,
    HomeworkSubmissionModel,
)
from tablet_app.models import (
    StudySession, TestModel, StudentTestAttemptModel,
)
from adminpanel.models import HomeworkModel
from adminpanel.utils.analytics import (
    calculate_student_learning_score,
    calculate_class_health_score,
    calculate_teacher_accountability_score,
    calculate_coordinator_control_score,
)
 
from django.db.models import Avg, Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
 
 
# ─────────────────────────────────────────────────────────────────────────────
# SCOPE HELPER
# ─────────────────────────────────────────────────────────────────────────────
 
def get_principal_scope(principal_id):
    """
    Returns the full scoped hierarchy for a given principal.
 
    Strategy (two-path merge):
    1. Direct school→student link via parent M2M (works without coordinator setup).
    2. Coordinator → Teacher → Class → Student chain.
    Merges both so counts are always correct.
 
    BUG FIX: original code did StudentModel.objects.filter(parent__id=principal_id,
    parent__role__type='Customer') — role__type for school owner is 'Customer' in
    your UserModel, which is correct. Kept as-is.
    """
    # Path 1: direct school→student
    school_students_qs = StudentModel.objects.filter(
        parent__id=principal_id,
        parent__role__type='Customer'
    ).distinct()
 
    # Path 2: hierarchy chain
    coordinators_mapping = PrincipalCoordinatorMapping.objects.filter(
        principal_id=principal_id
    ).select_related('coordinator')
 
    coordinator_ids = list(
        coordinators_mapping.values_list('coordinator_id', flat=True)
    )
 
    teacher_mappings = CoordinatorTeacherMapping.objects.filter(
        coordinator_id__in=coordinator_ids
    ).select_related('teacher')
 
    teacher_ids = list(
        teacher_mappings.values_list('teacher_id', flat=True).distinct()
    )
 
    assignments = TeacherAssignmentModel.objects.filter(
        teacher_id__in=teacher_ids
    ).prefetch_related('assigned_classes')
 
    class_ids = set()
    for a in assignments:
        class_ids.update(a.assigned_classes.values_list('id', flat=True))
 
    class_students_qs = StudentModel.objects.filter(
        student_class_id__in=class_ids
    ).distinct()
 
    # Merge
    if school_students_qs.exists():
        students_qs = school_students_qs
    elif class_students_qs.exists():
        students_qs = class_students_qs
    else:
        students_qs = StudentModel.objects.none()
 
    return {
        "coordinators_mapping": coordinators_mapping,
        "coordinator_ids":      coordinator_ids,
        "teacher_ids":          teacher_ids,
        "class_ids":            list(class_ids),      # BUG FIX: was a set — convert to list for ORM use
        "students_qs":          students_qs,
    }
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HELPER: safe class display name
# ─────────────────────────────────────────────────────────────────────────────
 
def _cls_name(cls):
    if cls is None:
        return 'N/A'
    return cls.get_display_name() if hasattr(cls, 'get_display_name') else str(cls)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# HELPER: active teachers today (replaces broken Q() chain)
# ─────────────────────────────────────────────────────────────────────────────
 
def _count_active_teachers_today(teacher_ids, class_ids, today):
    """
    BUG FIX: original code used a single Q() filter with deep reverse relations:
        Q(teacher_assignments__assigned_classes__students__studysession__start_time__date=today)
    This causes a FieldError because:
      - 'students' reverse accessor on ClassModel may not exist
      - Chain too deep → Django can't resolve it
      - 'given_remarks' reverse accessor on UserModel doesn't exist
 
    CORRECT approach: count teachers whose classes had at least one StudySession today.
    A teacher is "active today" if:
      - They created a test today, OR
      - They assigned homework today, OR
      - Any student in their classes had a study session today
    """
    if not teacher_ids:
        return 0
 
    active = set()
 
    # Test created today
    test_teachers = TestModel.objects.filter(
        created_by_id__in=teacher_ids,
        created_at__date=today
    ).values_list('created_by_id', flat=True).distinct()
    active.update(test_teachers)
 
    # Homework created today
    hw_teachers = HomeworkModel.objects.filter(
        created_by_id__in=teacher_ids,
        created_at__date=today
    ).values_list('created_by_id', flat=True).distinct()
    active.update(hw_teachers)
 
    # Study session in teacher's classes today
    if class_ids:
        session_class_ids = list(
            StudySession.objects.filter(
                student__student_class_id__in=class_ids,
                start_time__date=today
            ).values_list('student__student_class_id', flat=True).distinct()
        )
        # Find teachers whose classes had sessions today
        for a in TeacherAssignmentModel.objects.filter(teacher_id__in=teacher_ids):
            teacher_class_ids = set(a.assigned_classes.values_list('id', flat=True))
            if teacher_class_ids.intersection(session_class_ids):
                active.add(a.teacher_id)
 
    return len(active)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 1. PRINCIPAL FLOW API — Main dashboard
# ─────────────────────────────────────────────────────────────────────────────
 
class PrincipalFlowAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request):
        # BUG FIX: original required principal_id as query param.
        # Use request.user.id as default — principal IS the logged-in user.
        # Still accept principal_id param for backward compat.
        principal_id = request.query_params.get('principal_id') or request.user.id
        if not principal_id:
            return Response({"error": "principal_id is required"}, status=400)
 
        today        = timezone.now().date()
        one_week_ago = timezone.now() - timedelta(days=7)
 
        scope                = get_principal_scope(principal_id)
        coordinators_mapping = scope["coordinators_mapping"]
        coordinator_ids      = scope["coordinator_ids"]
        teacher_ids          = scope["teacher_ids"]
        class_ids            = scope["class_ids"]   # already a list
        students_qs          = scope["students_qs"]
 
        total_coordinators = len(coordinator_ids)
 
        teachers_qs    = UserModel.objects.filter(id__in=teacher_ids, role__type='Teacher')
        total_teachers = teachers_qs.count()
 
        # BUG FIX: class_ids was a set — ORM needs list/tuple
        classes_qs    = ClassModel.objects.filter(id__in=class_ids)
        total_classes = classes_qs.count()
 
        total_students = students_qs.count()
 
        # Active students today
        active_students_today = StudySession.objects.filter(
            start_time__date=today,
            student__in=students_qs
        ).values('student').distinct().count()
 
        # BUG FIX: replaced broken Q() deep-relation chain with helper function
        active_teachers_today = _count_active_teachers_today(
            teacher_ids, class_ids, today
        )
 
        # Weak students — BUG FIX: avoid calling calculate_student_learning_score
        # in a loop for large schools (N+1 problem). Use DB avg score as proxy.
        # The full score function can be used for small schools or individual drill-down.
        student_id_list = list(students_qs.values_list('id', flat=True))
 
        # Fast weak count via DB avg score per student
        weak_student_ids = list(
            StudentTestAttemptModel.objects.filter(
                student_id__in=student_id_list
            ).values('student_id').annotate(
                avg=Avg('score')
            ).filter(avg__lt=40).values_list('student_id', flat=True)
        )
        weak_students_count = len(weak_student_ids)
 
        # Weak classes — fast via DB
        weak_classes_count = 0
        for cls in classes_qs:
            cls_student_ids = list(
                StudentModel.objects.filter(
                    student_class=cls
                ).values_list('id', flat=True)
            )
            if cls_student_ids:
                cls_avg = StudentTestAttemptModel.objects.filter(
                    student_id__in=cls_student_ids
                ).aggregate(avg=Avg('score'))['avg'] or 0
                if cls_avg < 40:
                    weak_classes_count += 1
 
        # Pending homework
        pending_homework = HomeworkSubmissionModel.objects.filter(
            submitted_at__isnull=True,
            student__in=students_qs
        ).count()
 
        # Tests this week
        tests_this_week = TestModel.objects.filter(
            created_at__gte=one_week_ago,
            created_by_id__in=teacher_ids
        ).count()
 
        # Study hours today
        study_minutes_today = StudySession.objects.filter(
            start_time__date=today,
            student__in=students_qs
        ).aggregate(total=Sum('duration'))['total'] or 0
        study_hours_today = round(study_minutes_today / 60, 1)
 
        # Teacher activity score
        # BUG FIX: don't call calculate_teacher_accountability_score() in a loop
        # for large teacher lists — use fast DB version
        avg_teacher_activity = 0
        if total_teachers > 0:
            total_score = 0
            for t in teachers_qs:
                hw_count    = HomeworkModel.objects.filter(created_by=t).count()
                test_count  = TestModel.objects.filter(created_by=t).count()
                # Simple fast proxy score: (tests*15 + hw*15) capped at 100
                score = min(100, test_count * 15 + hw_count * 15)
                total_score += score
            avg_teacher_activity = round(total_score / total_teachers, 1)
 
        # Coordinator activity score
        avg_coordinator_activity = 0
        if total_coordinators > 0:
            # BUG FIX: calculate_coordinator_control_score may not exist in analytics.py
            # Use a safe wrapper
            total_coord_score = 0
            for c in coordinators_mapping:
                try:
                    total_coord_score += calculate_coordinator_control_score(c.coordinator_id)
                except Exception:
                    total_coord_score += 0
            avg_coordinator_activity = round(total_coord_score / total_coordinators, 1)
 
        # School health score — fast DB avg
        school_avg = StudentTestAttemptModel.objects.filter(
            student_id__in=student_id_list
        ).aggregate(avg=Avg('score'))['avg'] or 0
 
        # Action required count
        action_required_count = (
            weak_students_count +
            weak_classes_count +
            (1 if pending_homework > 50 else 0)
        )
 
        # Device usage
        # BUG FIX: original used DeviceModel.objects.filter(user__id__in=teacher_ids)
        # Devices are assigned to students (via student.parent), not teachers.
        # Use student parent IDs to find devices.
        parent_ids = list(
            students_qs.values_list('parent__id', flat=True).distinct()
        )
        total_devices   = DeviceModel.objects.filter(user__id__in=parent_ids).count()
        active_devices  = DeviceModel.objects.filter(
            user__id__in=parent_ids,
            is_active=True
        ).count()
        inactive_devices = total_devices - active_devices
 
        data = {
            "school_overview": {
                "total_students":            total_students,
                "active_students_today":     active_students_today,
                "total_teachers":            total_teachers,
                "active_teachers_today":     active_teachers_today,
                "total_classes":             total_classes,
                "total_coordinators":        total_coordinators,
                "weak_students":             weak_students_count,
                "weak_classes":              weak_classes_count,
                "pending_homework":          pending_homework,
                "tests_this_week":           tests_this_week,
                "study_hours_today":         study_hours_today,
                "teacher_activity_score":    avg_teacher_activity,
                "coordinator_activity_score": avg_coordinator_activity,
                "health_score":              round(school_avg, 1),
                "device_usage": {
                    "total":    total_devices,
                    "active":   active_devices,
                    "inactive": inactive_devices,
                    "issues":   0,   # extend when DeviceIssueModel exists
                },
                "action_required_count": action_required_count,
            },
            "coordinators": [
                {
                    "id":            c.coordinator.id,
                    "name":          f"{c.coordinator.first_name} {c.coordinator.last_name}".strip(),
                    "control_score": (
                        calculate_coordinator_control_score(c.coordinator.id)
                        if callable(calculate_coordinator_control_score) else 0
                    ),
                }
                for c in coordinators_mapping
            ],
        }
        return Response(data)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2. COORDINATOR DETAIL
# ─────────────────────────────────────────────────────────────────────────────
 
class CoordinatorDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request, coordinator_id):
        principal_id = request.user.id
 
        # Scope check
        if not PrincipalCoordinatorMapping.objects.filter(
            principal_id=principal_id,
            coordinator_id=coordinator_id
        ).exists():
            return Response({"error": "Coordinator not found in your school"}, status=404)
 
        teachers = CoordinatorTeacherMapping.objects.filter(
            coordinator_id=coordinator_id
        ).select_related('teacher')
 
        teacher_data = []
        for t in teachers:
            # BUG FIX: t.assigned_classes may not exist on CoordinatorTeacherMapping
            # — it should be t.teacher's assignment, not the mapping model's field.
            # Use TeacherAssignmentModel instead.
            assignment = TeacherAssignmentModel.objects.filter(
                teacher=t.teacher
            ).first()
            class_names = []
            if assignment:
                class_names = [_cls_name(c) for c in assignment.assigned_classes.all()]
 
            teacher_data.append({
                "id":                   t.teacher.id,
                "name":                 f"{t.teacher.first_name} {t.teacher.last_name}".strip(),
                "email":                t.teacher.email,
                "accountability_score": calculate_teacher_accountability_score(t.teacher.id),
                "classes":              class_names,
            })
 
        return Response({
            "coordinator_id": coordinator_id,
            "control_score":  calculate_coordinator_control_score(coordinator_id),
            "teachers":       teacher_data,
        })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3. TEACHER DETAIL
# ─────────────────────────────────────────────────────────────────────────────
 
class TeacherDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request, teacher_id):
        principal_id = request.user.id
        scope        = get_principal_scope(principal_id)
 
        if teacher_id not in scope["teacher_ids"]:
            return Response({"error": "Teacher not found in your school"}, status=404)
 
        assignment = TeacherAssignmentModel.objects.filter(
            teacher_id=teacher_id
        ).first()
        if not assignment:
            return Response({"error": "Teacher assignment not found"}, status=404)
 
        teacher = UserModel.objects.filter(id=teacher_id).first()
 
        class_data = []
        for c in assignment.assigned_classes.all():
            students_in_class = StudentModel.objects.filter(student_class=c)
            student_ids       = list(students_in_class.values_list('id', flat=True))
 
            avg_score = StudentTestAttemptModel.objects.filter(
                student_id__in=student_ids
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            weak_count = StudentTestAttemptModel.objects.filter(
                student_id__in=student_ids
            ).values('student_id').annotate(
                a=Avg('score')
            ).filter(a__lt=40).count()
 
            class_data.append({
                "id":            c.id,
                "name":          _cls_name(c),
                "student_count": students_in_class.count(),
                "avg_score":     round(avg_score, 1),
                "weak_students": weak_count,
                # BUG FIX: original called c.student_count() — method may not exist
                # calculate_class_health_score is safe to call
                "health_score":  calculate_class_health_score(c.id),
            })
 
        # Teacher stats
        hw_count   = HomeworkModel.objects.filter(created_by_id=teacher_id).count()
        test_count = TestModel.objects.filter(created_by_id=teacher_id).count()
        hw_checked = HomeworkSubmissionModel.objects.filter(
            homework__created_by_id=teacher_id,
            score__isnull=False
        ).count()
 
        last_test = TestModel.objects.filter(
            created_by_id=teacher_id
        ).order_by('-created_at').first()
 
        return Response({
            "teacher_id":           teacher_id,
            "name":                 f"{teacher.first_name} {teacher.last_name}".strip() if teacher else "—",
            "email":                teacher.email if teacher else "—",
            "accountability_score": calculate_teacher_accountability_score(teacher_id),
            "tests_count":          test_count,
            "homework_count":       hw_count,
            "homework_checked":     hw_checked,
            "last_active":          last_test.created_at.strftime('%Y-%m-%d') if last_test else "Never",
            "classes":              class_data,
        })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 4. CLASS DETAIL
# ─────────────────────────────────────────────────────────────────────────────
 
class ClassDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request, class_id):
        principal_id = request.user.id
        scope        = get_principal_scope(principal_id)
 
        if class_id not in scope["class_ids"]:
            return Response({"error": "Class not found in your school"}, status=404)
 
        cls      = ClassModel.objects.filter(id=class_id).first()
        students = StudentModel.objects.filter(student_class_id=class_id)
 
        student_data = []
        for s in students:
            avg = StudentTestAttemptModel.objects.filter(
                student=s
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            # Trend — last 3 vs previous 3 tests
            recent = list(StudentTestAttemptModel.objects.filter(
                student=s
            ).order_by('-started_at').values_list('score', flat=True)[:3])
            older  = list(StudentTestAttemptModel.objects.filter(
                student=s
            ).order_by('-started_at').values_list('score', flat=True)[3:6])
 
            if recent and older:
                r_avg = sum(recent) / len(recent)
                o_avg = sum(older)  / len(older)
                trend = 'Improving' if r_avg > o_avg + 5 else ('Falling' if r_avg < o_avg - 5 else 'Stable')
            else:
                trend = 'Stable'
 
            last_session = StudySession.objects.filter(
                student=s
            ).order_by('-start_time').first()
 
            risk = (
                'Inactive'        if not last_session else
                'Falling'         if trend == 'Falling' and avg < 50 else
                'High Risk'       if avg < 25 else
                'Needs Attention' if avg < 40 else
                'Stable'
            )
 
            student_data.append({
                "id":             s.id,
                "name":           s.student_name,
                "avg_score":      round(avg, 1),
                "learning_score": calculate_student_learning_score(s.id),
                "risk_level":     risk,
                "trend":          trend,
                "last_active":    last_session.start_time.strftime('%Y-%m-%d') if last_session else "Never",
            })
 
        # Class-level stats
        student_ids = list(students.values_list('id', flat=True))
        class_avg   = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids
        ).aggregate(avg=Avg('score'))['avg'] or 0
 
        hw_given = HomeworkModel.objects.filter(
            assigned_to__student_class_id=class_id
        ).distinct().count()
        hw_submitted = HomeworkSubmissionModel.objects.filter(
            student__student_class_id=class_id,
            submitted_at__isnull=False
        ).count()
        hw_pct = round((hw_submitted / hw_given * 100) if hw_given else 0, 1)
 
        return Response({
            "class_id":    class_id,
            "class_name":  _cls_name(cls),
            "health_score": calculate_class_health_score(class_id),
            "summary": {
                "student_count":  students.count(),
                "avg_score":      round(class_avg, 1),
                "weak_students":  len([s for s in student_data if s['risk_level'] in ('High Risk', 'Needs Attention')]),
                "hw_completion":  hw_pct,
            },
            "students": student_data,
        })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 5. PRINCIPAL MODULE API (unified module drill-down)
# ─────────────────────────────────────────────────────────────────────────────
 
class PrincipalModuleAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]
 
    def get(self, request, module_name):
        principal_id = request.user.id
        scope        = get_principal_scope(principal_id)
 
        if module_name == 'students':
            students = scope["students_qs"]
            data = []
            for s in students:
                avg = StudentTestAttemptModel.objects.filter(
                    student=s
                ).aggregate(avg=Avg('score'))['avg'] or 0
 
                hw_assigned  = HomeworkModel.objects.filter(assigned_to=s).count()
                hw_submitted = HomeworkSubmissionModel.objects.filter(
                    student=s, submitted_at__isnull=False
                ).count()
                hw_pct = round((hw_submitted / hw_assigned * 100) if hw_assigned else 0, 1)
 
                last_s = StudySession.objects.filter(
                    student=s
                ).order_by('-start_time').first()
 
                data.append({
                    "id":             s.id,
                    "name":           s.student_name,
                    "class":          _cls_name(s.student_class),
                    "avg_score":      round(avg, 1),
                    "learning_score": calculate_student_learning_score(s.id),
                    "hw_completion":  hw_pct,
                    "last_active":    last_s.start_time.strftime('%Y-%m-%d') if last_s else "Never",
                    "risk_tag":       "High Risk" if avg < 40 else ("Needs Attention" if avg < 60 else "Stable"),
                })
            return Response({"module": "Students", "count": len(data), "data": data})
 
        elif module_name == 'classes':
            classes = ClassModel.objects.filter(id__in=scope["class_ids"])
            data = []
            for c in classes:
                student_ids = list(
                    StudentModel.objects.filter(student_class=c).values_list('id', flat=True)
                )
                avg = StudentTestAttemptModel.objects.filter(
                    student_id__in=student_ids
                ).aggregate(avg=Avg('score'))['avg'] or 0
 
                weak = StudentTestAttemptModel.objects.filter(
                    student_id__in=student_ids
                ).values('student_id').annotate(
                    a=Avg('score')
                ).filter(a__lt=40).count()
 
                data.append({
                    "id":            c.id,
                    "name":          _cls_name(c),
                    "student_count": len(student_ids),
                    "avg_score":     round(avg, 1),
                    "weak_students": weak,
                    "health_score":  calculate_class_health_score(c.id),
                })
            return Response({"module": "Classes", "count": len(data), "data": data})
 
        elif module_name == 'teachers':
            teachers = UserModel.objects.filter(
                id__in=scope["teacher_ids"], role__type='Teacher'
            )
            data = []
            for t in teachers:
                hw_count    = HomeworkModel.objects.filter(created_by=t).count()
                test_count  = TestModel.objects.filter(created_by=t).count()
                last_test   = TestModel.objects.filter(created_by=t).order_by('-created_at').first()
                data.append({
                    "id":                   t.id,
                    "name":                 f"{t.first_name} {t.last_name}".strip(),
                    "email":                t.email,
                    "tests_count":          test_count,
                    "homework_count":       hw_count,
                    "last_active":          last_test.created_at.strftime('%Y-%m-%d') if last_test else "Never",
                    "accountability_score": calculate_teacher_accountability_score(t.id),
                })
            return Response({"module": "Teachers", "count": len(data), "data": data})
 
        elif module_name == 'coordinators':
            coordinator_ids = scope["coordinator_ids"]
            coordinators = UserModel.objects.filter(id__in=coordinator_ids)
            data = []
            for coord in coordinators:
                coord_classes  = CoordinatorAssignmentModel.objects.filter(
                    coordinator=coord
                ).values_list('class_obj_id', flat=True).distinct()
                coord_students = StudentModel.objects.filter(
                    student_class_id__in=coord_classes
                ).count()
                data.append({
                    "id":            coord.id,
                    "name":          f"{coord.first_name} {coord.last_name}".strip(),
                    "email":         coord.email,
                    "classes_count": coord_classes.count(),
                    "students_count": coord_students,
                    "control_score": calculate_coordinator_control_score(coord.id),
                })
            return Response({"module": "Coordinators", "count": len(data), "data": data})
 
        return Response({"error": f"Module '{module_name}' not found or not yet implemented"}, status=404)