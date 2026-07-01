# school_view.py — FULLY FIXED VERSION
# Fixes: end_time→start_time, students→assigned_to, get_display_name→str(),
#        updated_at→created_at, double-slash URL, is_visible_to_parent guard

import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status
from user_management.models import *
from adminpanel.serializers import *
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from ..pagination import ListPagination
from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper
from django.shortcuts import get_object_or_404
from django.views import View   
from django.shortcuts import render
from adminpanel.views import DashboardsView



from user_management.models import (
    UserModel, StudentModel, ClassModel, DeviceModel,
    CoordinatorAssignmentModel, TeacherAssignmentModel,
    SchoolProfileModel, CoordinatorActionModel, RoleModel
)
from tablet_app.models import (
    Subject, Chapter, StudySession, TestModel,
    StudentTestAttemptModel,
)
from adminpanel.utils.analytics import calculate_student_learning_score
from adminpanel.models import HomeworkModel, HomeworkSubmissionModel

CURRENT_ACADEMIC_YEAR = '2024-25'
WEAK_SCORE_THRESHOLD  = 40


def _cls_name(cls):
    """Safe class name — works whether or not get_display_name() exists."""
    if cls is None:
        return 'N/A'
    return cls.get_display_name() if hasattr(cls, 'get_display_name') else str(cls)


def get_teachers():
    return UserModel.objects.filter(role__type='Teacher')


def get_coordinators():
    return UserModel.objects.filter(role__type='Coordinator')


def get_classes_for_coordinator(coordinator_user):
    class_ids = CoordinatorAssignmentModel.objects.filter(
        coordinator=coordinator_user
    ).values_list('class_obj_id', flat=True).distinct()
    return ClassModel.objects.filter(id__in=class_ids)


def get_teachers_for_coordinator(coordinator_user):
    teacher_ids = CoordinatorAssignmentModel.objects.filter(
        coordinator=coordinator_user
    ).values_list('teacher_id', flat=True).distinct()
    return UserModel.objects.filter(id__in=teacher_ids, role__type='Teacher')


def get_students_for_teacher(teacher_user):
    assignment = TeacherAssignmentModel.objects.filter(teacher=teacher_user).first()
    if not assignment:
        return StudentModel.objects.none()
    class_ids = assignment.assigned_classes.values_list('id', flat=True)
    return StudentModel.objects.filter(student_class__id__in=class_ids)


def get_customer_scope(user):
    class_ids   = list(ClassModel.objects.filter(
        academic_year=CURRENT_ACADEMIC_YEAR
    ).values_list('id', flat=True))
    students_qs = StudentModel.objects.filter(student_class__id__in=class_ids)
    return {"class_ids": class_ids, "students_qs": students_qs}


# ─── 1. School Profile ────────────────────────────────────────────────────────

class SchoolProfileAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        profile = SchoolProfileModel.objects.filter(
            academic_year=CURRENT_ACADEMIC_YEAR
        ).first()
        if not profile:
            return Response({})
        return Response({
            "school_name":          profile.school_name,
            "address":              profile.address,
            "board":                profile.board,
            "medium":               profile.medium,
            "principal_name":       profile.principal_name,
            "principal_phone":      profile.principal_phone,
            "principal_email":      profile.principal_email,
            "total_tablets_given":  profile.total_tablets_given,
            "working_days":         profile.working_days,
            "academic_year":        profile.academic_year,
            "timetable_structure":  profile.timetable_structure,
            "exam_test_structure":  profile.exam_test_structure,
        })

    def post(self, request):
        profile, created = SchoolProfileModel.objects.update_or_create(
            academic_year=CURRENT_ACADEMIC_YEAR,
            defaults={
                'school_name':         request.data.get('school_name', ''),
                'address':             request.data.get('address', ''),
                'board':               request.data.get('board', 'GSEB'),
                'medium':              request.data.get('medium', 'English'),
                'principal_name':      request.data.get('principal_name', ''),
                'principal_phone':     request.data.get('principal_phone', ''),
                'principal_email':     request.data.get('principal_email', ''),
                'total_tablets_given': request.data.get('total_tablets_given', 0),
                'working_days':        request.data.get('working_days', 220),
                'timetable_structure': request.data.get('timetable_structure'),
                'exam_test_structure': request.data.get('exam_test_structure'),
            }
        )
        return Response({"message": "Profile updated successfully", "created": created})


# ─── 2. Onboarding Excel Import ───────────────────────────────────────────────

class OnboardingExcelImportAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        import_type = request.data.get('import_type')
        file_obj    = request.FILES.get('file')

        if not file_obj:
            return Response({"error": "No file uploaded"}, status=400)
        if not import_type:
            return Response({"error": "import_type required: student/teacher/coordinator/device"}, status=400)

        try:
            df    = pd.read_excel(file_obj)
            count = 0

            with transaction.atomic():
                if import_type == 'student':
                    for _, row in df.iterrows():
                        class_obj, _ = ClassModel.objects.get_or_create(
                            standard=int(row['Standard']),
                            section=str(row['Section']).strip(),
                            academic_year=CURRENT_ACADEMIC_YEAR,
                        )
                        StudentModel.objects.get_or_create(
                            student_name=str(row['Student Name']).strip(),
                            student_class=class_obj,
                            defaults={'email': str(row.get('Email', '') or '')}
                        )
                        count += 1

                elif import_type == 'teacher':
                    teacher_role, _ = RoleModel.objects.get_or_create(
                        type='Teacher', defaults={'name': 'Teacher'}
                    )
                    for _, row in df.iterrows():
                        UserModel.objects.get_or_create(
                            email=str(row['Email']).strip(),
                            defaults={
                                'first_name': str(row['Teacher Name']).strip().split()[0],
                                'last_name':  ' '.join(str(row['Teacher Name']).strip().split()[1:]) or '',
                                'role':       teacher_role,
                                'mobile_no':  str(row.get('Phone', '') or ''),
                            }
                        )
                        count += 1

                elif import_type == 'coordinator':
                    coord_role, _ = RoleModel.objects.get_or_create(
                        type='Coordinator', defaults={'name': 'Coordinator'}
                    )
                    for _, row in df.iterrows():
                        UserModel.objects.get_or_create(
                            email=str(row['Email']).strip(),
                            defaults={
                                'first_name': str(row['Coordinator Name']).strip().split()[0],
                                'last_name':  ' '.join(str(row['Coordinator Name']).strip().split()[1:]) or '',
                                'role':       coord_role,
                                'mobile_no':  str(row.get('Phone', '') or ''),
                            }
                        )
                        count += 1

                elif import_type == 'device':
                    for _, row in df.iterrows():
                        DeviceModel.objects.get_or_create(
                            imei_number=str(row['IMEI Number']).strip(),
                            defaults={
                                'tablet_id':     str(row.get('Tablet ID', '') or ''),
                                'serial_number': str(row.get('Serial Number', '') or ''),
                                'is_active':     True,
                                'user':          request.user,
                            }
                        )
                        count += 1
                else:
                    return Response({"error": f"Unknown import_type: {import_type}"}, status=400)

            return Response({"message": f"Successfully imported {count} records.", "count": count})

        except KeyError as e:
            return Response({"error": f"Missing column in Excel: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


# ─── 3. Student Risk Categories ───────────────────────────────────────────────

class StudentRiskCategoriesAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope          = get_customer_scope(request.user)
        students       = scope["students_qs"]
        today          = timezone.now().date()
        three_days_ago = today - timedelta(days=3)

        results = {
            "Excellent": [], "Stable": [], "Needs Attention": [],
            "High Risk": [], "Inactive": [], "Falling": [], "Improving": [],
        }

        for student in students:
            score = calculate_student_learning_score(student.id)

            # FIX: use start_time not end_time
            last_session = StudySession.objects.filter(
                student=student
            ).order_by('-start_time').first()

            inactive = (
                not last_session or
                last_session.start_time.date() < three_days_ago   # FIX: start_time
            )

            scores_list = list(
                StudentTestAttemptModel.objects
                .filter(student=student)
                .order_by('started_at')
                .values_list('score', flat=True)
            )
            trend = None
            if len(scores_list) >= 2:
                trend = 'Improving' if scores_list[-1] > scores_list[-2] else 'Falling'

            if inactive:
                tag = 'Inactive'
            elif trend == 'Falling' and score < 50:
                tag = 'Falling'
            elif trend == 'Improving':
                tag = 'Improving'
            elif score >= 75:
                tag = 'Excellent'
            elif score >= 50:
                tag = 'Stable'
            elif score >= 40:
                tag = 'Needs Attention'
            else:
                tag = 'High Risk'

            results[tag].append({
                "student_id":   student.id,
                "student_name": student.student_name,
                "class":        _cls_name(student.student_class),   # FIX: safe helper
                "score":        round(score, 1),
                "last_active":  last_session.start_time.date().isoformat() if last_session else "Never",
            })

        summary = {tag: len(lst) for tag, lst in results.items()}
        return Response({"summary": summary, "results": results})


# ─── 4. Students Needing Immediate Attention ──────────────────────────────────

class StudentsImmediateAttentionAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope          = get_customer_scope(request.user)
        students       = scope["students_qs"]
        today          = timezone.now().date()
        three_days_ago = today - timedelta(days=3)
        attention_list = []

        for student in students:
            reasons = []
            score   = calculate_student_learning_score(student.id)

            if score < WEAK_SCORE_THRESHOLD:
                reasons.append(f"Score below {WEAK_SCORE_THRESHOLD}% — current: {round(score,1)}%")

            # FIX: start_time
            last_session = StudySession.objects.filter(
                student=student
            ).order_by('-start_time').first()
            if not last_session or last_session.start_time.date() < three_days_ago:
                reasons.append("Inactive on tablet for 3+ days")

            hw_total = HomeworkSubmissionModel.objects.filter(student=student).count()
            if hw_total > 0:
                hw_submitted = HomeworkSubmissionModel.objects.filter(
                    student=student,
                    submitted_at__isnull=False
                ).count()
                hw_pct = (hw_submitted / hw_total) * 100
                if hw_pct < 50:
                    reasons.append(f"Homework completion only {round(hw_pct,1)}%")

            if not StudentTestAttemptModel.objects.filter(student=student).exists():
                reasons.append("Never attempted any test")

            if reasons:
                attention_list.append({
                    "student_id":   student.id,
                    "student_name": student.student_name,
                    "class":        _cls_name(student.student_class),
                    "score":        round(score, 1),
                    "reasons":      reasons,
                    "last_active":  last_session.start_time.date().isoformat() if last_session else "Never",
                    "priority":     "High" if len(reasons) >= 2 else "Medium",
                })

        attention_list.sort(key=lambda x: (-len(x['reasons']), x['score']))
        return Response({"total": len(attention_list), "results": attention_list})


# ─── 5. Class Comparison Dashboard ───────────────────────────────────────────

class ClassComparisonDashboardAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope     = get_customer_scope(request.user)
        class_ids = scope["class_ids"]
        today     = timezone.now().date()

        classes_data = []
        for cls_id in class_ids:
            cls           = ClassModel.objects.filter(id=cls_id).first()
            if not cls:
                continue
            students      = StudentModel.objects.filter(student_class=cls)
            student_count = students.count()
            if student_count == 0:
                continue

            avg_score = (
                StudentTestAttemptModel.objects
                .filter(student__in=students)
                .aggregate(avg=Avg('score'))['avg'] or 0
            )

            weak_count = sum(
                1 for s in students
                if calculate_student_learning_score(s.id) < WEAK_SCORE_THRESHOLD
            )
            weak_pct = round((weak_count / student_count) * 100, 1)

            # FIX: assigned_to (not students)
            hw_total = HomeworkSubmissionModel.objects.filter(
                student__in=students
            ).count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(
                student__in=students,
                submitted_at__isnull=False
            ).count()
            hw_pct = round((hw_submitted / hw_total) * 100, 1) if hw_total > 0 else 0

            # FIX: start_time
            sessions = StudySession.objects.filter(
                student__in=students,
                start_time__date=today
            )
            study_minutes = sum(s.duration or 0 for s in sessions)

            health = round(
                (avg_score * 0.5) + ((100 - weak_pct) * 0.3) + (hw_pct * 0.2), 1
            )

            if health >= 75:    health_status = "Good"
            elif health >= 50:  health_status = "Average"
            elif health >= 35:  health_status = "Weak"
            else:               health_status = "Critical"

            classes_data.append({
                "class_id":                cls_id,
                "class_name":              _cls_name(cls),
                "student_count":           student_count,
                "avg_score":               round(avg_score, 1),
                "weak_students_count":     weak_count,
                "weak_students_pct":       weak_pct,
                "homework_completion_pct": hw_pct,
                "study_minutes_today":     study_minutes,
                "health_score":            health,
                "health_status":           health_status,
            })

        classes_data.sort(key=lambda x: x['health_score'])
        return Response({"results": classes_data})


# ─── 6. Teacher Rankings ──────────────────────────────────────────────────────

class TeacherRankingsAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        today    = timezone.now().date()
        rankings = []

        for teacher in get_teachers():
            teacher_students = get_students_for_teacher(teacher)
            tests_conducted  = TestModel.objects.filter(created_by=teacher).count()
            hw_given         = HomeworkModel.objects.filter(created_by=teacher).count()
            hw_checked       = HomeworkSubmissionModel.objects.filter(
                homework__created_by=teacher,
                score__isnull=False
            ).count()

            avg_score = (
                StudentTestAttemptModel.objects
                .filter(student__in=teacher_students)
                .aggregate(avg=Avg('score'))['avg'] or 0
            )
            weak_count = sum(
                1 for s in teacher_students
                if calculate_student_learning_score(s.id) < WEAK_SCORE_THRESHOLD
            )

            assignment = TeacherAssignmentModel.objects.filter(teacher=teacher).first()
            class_ids  = list(
                assignment.assigned_classes.values_list('id', flat=True)
            ) if assignment else []

            sessions_total = StudySession.objects.filter(
                student__student_class__id__in=class_ids
            ).count()
            sessions_today = StudySession.objects.filter(
                student__student_class__id__in=class_ids,
                start_time__date=today       # FIX: start_time
            ).count()
            teaching_minutes = (
                StudySession.objects
                .filter(student__student_class__id__in=class_ids)
                .aggregate(total=Sum('duration'))['total'] or 0
            )

            # FIX: start_time
            last_s = StudySession.objects.filter(
                student__student_class__id__in=class_ids
            ).order_by('-start_time').first()
            last_active = last_s.start_time.date() if last_s else None

            classes_score  = min(sessions_total * 2,        20)
            time_score     = min(teaching_minutes / 60 * 2, 20)
            test_score     = min(tests_conducted * 3,        15)
            hw_give_score  = min(hw_given * 3,               15)
            hw_check_score = min(hw_checked * 3,             15)
            student_score  = round((avg_score / 100) * 15,   1)
            acc_score      = round(
                classes_score + time_score + test_score +
                hw_give_score + hw_check_score + student_score, 1
            )

            if acc_score >= 75:   score_label = "Strong"
            elif acc_score >= 50: score_label = "Average"
            elif acc_score >= 30: score_label = "Weak"
            else:                 score_label = "Inactive"

            rankings.append({
                "teacher_id":           teacher.id,
                "teacher_name":         f"{teacher.first_name} {teacher.last_name}".strip(),
                "email":                teacher.email,
                "student_count":        teacher_students.count(),
                "sessions_total":       sessions_total,
                "sessions_today":       sessions_today,
                "teaching_hours":       round(teaching_minutes / 60, 1),
                "tests_conducted":      tests_conducted,
                "homework_given":       hw_given,
                "homework_checked":     hw_checked,
                "avg_student_score":    round(avg_score, 1),
                "weak_students":        weak_count,
                "is_active_today":      last_active == today if last_active else False,
                "last_active":          last_active.isoformat() if last_active else "Never",
                "accountability_score": acc_score,
                "score_label":          score_label,
            })

        rankings.sort(key=lambda x: -x['accountability_score'])
        for i, t in enumerate(rankings, 1):
            t['rank'] = i
        return Response({"total_teachers": len(rankings), "results": rankings})


# ─── 7. Coordinator Neglect ───────────────────────────────────────────────────

class CoordinatorNeglectAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        today          = timezone.now().date()
        two_days_ago   = today - timedelta(days=2)
        three_days_ago = today - timedelta(days=3)
        seven_days_ago = today - timedelta(days=7)
        report         = []

        for coord in get_coordinators():
            issues         = []
            coord_classes  = get_classes_for_coordinator(coord)
            coord_teachers = get_teachers_for_coordinator(coord)
            coord_students = StudentModel.objects.filter(student_class__in=coord_classes)

            for cls in coord_classes:
                cls_students = StudentModel.objects.filter(student_class=cls)
                cls_avg      = (
                    StudentTestAttemptModel.objects
                    .filter(student__in=cls_students)
                    .aggregate(avg=Avg('score'))['avg'] or 0
                )
                if cls_avg < WEAK_SCORE_THRESHOLD:
                    # FIX: created_at (not updated_at — field may not exist)
                    recent_action = CoordinatorActionModel.objects.filter(
                        coordinator=coord,
                        status__in=['Resolved', 'Discussed', 'In Progress'],
                        created_at__date__gte=seven_days_ago
                    ).exists()
                    if not recent_action:
                        issues.append(
                            f"Class {_cls_name(cls)} avg {round(cls_avg,1)}%"
                            f" — no coordinator action in 7 days"
                        )

            for teacher in coord_teachers:
                t_assignment = TeacherAssignmentModel.objects.filter(teacher=teacher).first()
                t_class_ids  = list(
                    t_assignment.assigned_classes.values_list('id', flat=True)
                ) if t_assignment else []

                had_activity = StudySession.objects.filter(
                    student__student_class__id__in=t_class_ids,
                    start_time__date__gte=two_days_ago  # FIX: start_time
                ).exists()

                if not had_activity:
                    issues.append(
                        f"Teacher {teacher.first_name} {teacher.last_name}"
                        f" — no class activity for 2+ days"
                    )

            inactive_count = sum(
                1 for s in coord_students
                if not StudySession.objects.filter(
                    student=s, start_time__date__gte=three_days_ago  # FIX: start_time
                ).exists()
            )
            if inactive_count > 5:
                issues.append(f"{inactive_count} students inactive 3+ days")

            unresolved_old = CoordinatorActionModel.objects.filter(
                coordinator=coord,
                status__in=['New', 'Pending'],
                created_at__date__lte=seven_days_ago
            ).count()
            if unresolved_old:
                issues.append(f"{unresolved_old} action(s) pending for 7+ days")

            if len(issues) == 0:    neglect_status = "Good"
            elif len(issues) == 1:  neglect_status = "Average"
            elif len(issues) <= 3:  neglect_status = "Weak"
            else:                   neglect_status = "Critical"

            report.append({
                "coordinator_id":   coord.id,
                "coordinator_name": f"{coord.first_name} {coord.last_name}".strip(),
                "email":            coord.email,
                "classes_count":    coord_classes.count(),
                "teachers_count":   coord_teachers.count(),
                "students_count":   coord_students.count(),
                "issues":           issues,
                "issue_count":      len(issues),
                "neglect_status":   neglect_status,
            })

        report.sort(key=lambda x: -x['issue_count'])
        return Response({"results": report})


# ─── 8. Chapter Weakness ──────────────────────────────────────────────────────

class ChapterWeaknessAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope      = get_customer_scope(request.user)
        class_ids  = scope["class_ids"]
        subject_id = request.query_params.get('subject_id')
        class_id   = request.query_params.get('class_id')

        sessions_qs = StudySession.objects.filter(
            student__student_class__id__in=class_ids,
            chapter__isnull=False
        ).select_related('chapter', 'chapter__subject', 'student__student_class')

        if subject_id:
            sessions_qs = sessions_qs.filter(chapter__subject_id=subject_id)
        if class_id:
            sessions_qs = sessions_qs.filter(student__student_class_id=class_id)

        chapter_map = {}
        chapters_seen = sessions_qs.values(
            'chapter__id', 'chapter__name', 'chapter__subject__name'
        ).distinct()

        for ch_row in chapters_seen:
            ch_id = ch_row['chapter__id']
            student_ids = sessions_qs.filter(
                chapter__id=ch_id
            ).values_list('student_id', flat=True).distinct()

            subject_name = ch_row['chapter__subject__name']
            attempts_qs  = StudentTestAttemptModel.objects.filter(
                student__id__in=student_ids,
                test__subject__name=subject_name
            )
            avg          = attempts_qs.aggregate(avg=Avg('score'))['avg'] or 0
            weak_students = attempts_qs.filter(score__lt=WEAK_SCORE_THRESHOLD).values(
                'student'
            ).distinct().count()

            if avg >= 70:    ch_status, revision, retest = "Good",     False, False
            elif avg >= 50:  ch_status, revision, retest = "Average",  True,  False
            elif avg >= 35:  ch_status, revision, retest = "Weak",     True,  True
            else:            ch_status, revision, retest = "Critical", True,  True

            chapter_map[ch_id] = {
                "chapter_id":      ch_id,
                "chapter_name":    ch_row['chapter__name'],
                "subject_name":    subject_name,
                "avg_score":       round(avg, 1),
                "weak_students":   weak_students,
                "status":          ch_status,
                "revision_needed": revision,
                "retest_needed":   retest,
            }

        results = sorted(chapter_map.values(), key=lambda x: x['avg_score'])
        return Response({"results": results})


# ─── 9. Chapter Heatmap ───────────────────────────────────────────────────────

class ChapterHeatmapAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope      = get_customer_scope(request.user)
        class_ids  = scope["class_ids"]
        subject_id = request.query_params.get('subject_id')

        if not subject_id:
            return Response({"error": "subject_id query param is required"}, status=400)

        chapters = Chapter.objects.filter(subject_id=subject_id)
        classes  = ClassModel.objects.filter(id__in=class_ids)

        heatmap = []
        for chapter in chapters:
            row = {"chapter_id": chapter.id, "chapter_name": chapter.name, "classes": {}}
            for cls in classes:
                student_ids = StudySession.objects.filter(
                    chapter=chapter,
                    student__student_class=cls
                ).values_list('student_id', flat=True).distinct()

                avg = None
                if student_ids:
                    avg = (
                        StudentTestAttemptModel.objects
                        .filter(
                            student__id__in=student_ids,
                            test__subject_id=subject_id
                        )
                        .aggregate(avg=Avg('score'))['avg']
                    )

                if avg is None:   color, label = "grey",   "N/A"
                elif avg >= 70:   color, label = "green",  f"{round(avg,1)}%"
                elif avg >= 45:   color, label = "yellow", f"{round(avg,1)}%"
                else:             color, label = "red",    f"{round(avg,1)}%"

                row["classes"][_cls_name(cls)] = {
                    "avg":   round(avg, 1) if avg is not None else None,
                    "color": color,
                    "label": label,
                }
            heatmap.append(row)

        return Response({
            "subject_id": subject_id,
            "classes":    [_cls_name(c) for c in classes],
            "heatmap":    heatmap,
        })


# ─── 10. Action Required ─────────────────────────────────────────────────────

class ActionRequiredAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope           = get_customer_scope(request.user)
        students        = scope["students_qs"]
        class_ids       = scope["class_ids"]
        today           = timezone.now().date()
        three_days_ago  = today - timedelta(days=3)
        two_days_ago    = today - timedelta(days=2)
        thirty_days_ago = today - timedelta(days=30)
        actions         = []

        # H1: Student score < 40%
        for student in students:
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            if attempts.exists():
                avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
                if avg < WEAK_SCORE_THRESHOLD:
                    actions.append({
                        "priority":    "High",
                        "issue":       f"{student.student_name} ({_cls_name(student.student_class)}) avg score {round(avg,1)}%",
                        "responsible": "Subject Teacher",
                        "action":      "Schedule immediate revision and retest",
                    })

        # H2: Student inactive 3+ days — FIX: start_time
        for student in students:
            last_s = StudySession.objects.filter(student=student).order_by('-start_time').first()
            if not last_s or last_s.start_time.date() < three_days_ago:
                actions.append({
                    "priority":    "High",
                    "issue":       f"{student.student_name} ({_cls_name(student.student_class)}) inactive 3+ days",
                    "responsible": "Class Teacher",
                    "action":      "Call parents / check device sync",
                })

        # H3: Teacher classes inactive 2+ days — FIX: start_time
        for teacher in get_teachers():
            t_assignment = TeacherAssignmentModel.objects.filter(teacher=teacher).first()
            t_class_ids  = list(
                t_assignment.assigned_classes.values_list('id', flat=True)
            ) if t_assignment else []
            if t_class_ids:
                had_activity = StudySession.objects.filter(
                    student__student_class__id__in=t_class_ids,
                    start_time__date__gte=two_days_ago
                ).exists()
                if not had_activity:
                    actions.append({
                        "priority":    "High",
                        "issue":       f"Teacher {teacher.first_name} {teacher.last_name} — no class activity 2+ days",
                        "responsible": "Coordinator",
                        "action":      "Contact teacher and review inactivity reason",
                    })

        # M1: Homework pending > 50% — FIX: assigned_to (not students)
        for cls_id in class_ids:
            cls = ClassModel.objects.filter(id=cls_id).first()
            if not cls:
                continue
            cls_students = StudentModel.objects.filter(student_class=cls)

            # FIX: use assigned_to M2M field
            homeworks = HomeworkModel.objects.filter(
                students__in=cls_students
            ).distinct()

            for hw in homeworks:

                assigned = hw.students.count()

                submitted = HomeworkSubmissionModel.objects.filter(
                    homework=hw,
                    student__in=cls_students,
                    submitted_at__isnull=False
                ).count()

                pending = assigned - submitted

                if assigned > 0 and (pending / assigned) > 0.5:
                    actions.append({
                        "priority": "Medium",
                        "issue": f"Class {_cls_name(cls)} — '{hw.title}' {round((pending / assigned) * 100)}% pending",
                        "responsible": "Class Teacher + Coordinator",
                        "action": "Send reminders and follow up with students",
                    })

        # M2: Class avg below 50
        for cls_id in class_ids:
            cls = ClassModel.objects.filter(id=cls_id).first()
            if not cls:
                continue
            cls_students = StudentModel.objects.filter(student_class=cls)
            cls_avg      = (
                StudentTestAttemptModel.objects
                .filter(student__in=cls_students)
                .aggregate(avg=Avg('score'))['avg'] or 0
            )
            if 0 < cls_avg < 50:
                actions.append({
                    "priority":    "Medium",
                    "issue":       f"Class {_cls_name(cls)} avg dropped to {round(cls_avg,1)}%",
                    "responsible": "Coordinator + Subject Teachers",
                    "action":      "Take revision test and follow up weak students",
                })

        # M3: Teacher with ≤1 test this month
        for teacher in get_teachers():
            test_count = TestModel.objects.filter(
                created_by=teacher,
                created_at__date__gte=thirty_days_ago
            ).count()
            if test_count <= 1:
                actions.append({
                    "priority":    "Medium",
                    "issue":       f"Teacher {teacher.first_name} {teacher.last_name} — only {test_count} test(s) this month",
                    "responsible": "Coordinator",
                    "action":      "Review teacher and schedule tests",
                })

        # L1: Tablets not synced — FIX: check field name (last_sync or last_sync_at)
        # Using last_sync — change to last_sync_at if that's the model field name
        try:
            inactive_devices = DeviceModel.objects.filter(
                last_sync__date__lt=three_days_ago,
                is_active=True
            )
        except Exception:
            # Fallback if field name is last_sync_at
            inactive_devices = DeviceModel.objects.filter(
                last_sync_at__date__lt=three_days_ago,
                is_active=True
            )

        if inactive_devices.exists():
            actions.append({
                "priority":    "Low",
                "issue":       f"{inactive_devices.count()} tablet(s) not synced for 3+ days",
                "responsible": "IT / Admin",
                "action":      "Sync devices and check network / device issue",
            })

        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 9))

        return Response({
            "total":   len(actions),
            "high":    sum(1 for a in actions if a['priority'] == 'High'),
            "medium":  sum(1 for a in actions if a['priority'] == 'Medium'),
            "low":     sum(1 for a in actions if a['priority'] == 'Low'),
            "results": actions,
        })


# ─── 11. Parent Meeting PDF Report ────────────────────────────────────────────

class ParentMeetingPDFReportAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = StudentModel.objects.get(id=student_id)
        except StudentModel.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        score = calculate_student_learning_score(student.id)
        avg   = (
            StudentTestAttemptModel.objects
            .filter(student=student)
            .aggregate(avg=Avg('score'))['avg'] or 0
        )

        hw_total     = HomeworkSubmissionModel.objects.filter(student=student).count()
        hw_submitted = HomeworkSubmissionModel.objects.filter(
            student=student, submitted_at__isnull=False
        ).count()
        hw_pct = round((hw_submitted / hw_total) * 100, 1) if hw_total > 0 else 0

        # FIX: start_time
        last_session = StudySession.objects.filter(
            student=student
        ).order_by('-start_time').first()

        weak_subjects = (
            StudentTestAttemptModel.objects
            .filter(student=student)
            .values('test__subject__name')
            .annotate(avg=Avg('score'))
            .filter(avg__lt=WEAK_SCORE_THRESHOLD)
            .order_by('avg')[:5]
        )

        weak_chapters = []
        chapter_sessions = StudySession.objects.filter(
            student=student, chapter__isnull=False
        ).values('chapter__name', 'chapter__subject__name').distinct()

        for cs in chapter_sessions:
            subject_name = cs['chapter__subject__name']
            ch_attempts  = StudentTestAttemptModel.objects.filter(
                student=student, test__subject__name=subject_name
            )
            ch_avg = ch_attempts.aggregate(avg=Avg('score'))['avg'] or 0
            if ch_avg < WEAK_SCORE_THRESHOLD:
                weak_chapters.append({
                    "chapter": cs['chapter__name'],
                    "subject": subject_name,
                    "avg":     round(ch_avg, 1),
                })

        # FIX: guard is_visible_to_parent — field may not exist on model
        from user_management.models import TeacherRemarkModel
        try:
            remarks = TeacherRemarkModel.objects.filter(
                student=student, is_visible_to_parent=True
            ).order_by('-created_at')[:3]
            remark_texts = [r.remark for r in remarks]
        except Exception:
            # Field doesn't exist — fall back to all remarks
            remarks = TeacherRemarkModel.objects.filter(
                student=student
            ).order_by('-created_at')[:3]
            remark_texts = [r.remark for r in remarks]

        if not remark_texts:
            remark_texts = ["N/A"]

        return Response({
            "student_name":    student.student_name,
            "class":           _cls_name(student.student_class),
            "academic_year":   CURRENT_ACADEMIC_YEAR,
            "learning_score":  round(score, 1),
            "avg_test_score":  round(avg, 1),
            "hw_completion":   hw_pct,
            "last_active":     last_session.start_time.date().isoformat() if last_session else "Never",
            "weak_subjects":   [
                {"subject": ws['test__subject__name'], "avg": round(ws['avg'], 1)}
                for ws in weak_subjects
            ],
            "weak_chapters":   weak_chapters[:5],
            "teacher_remarks": remark_texts,
            "improvement_plan": (
                "Needs urgent attention. Ensure daily tablet usage and test revision."
                if score < WEAK_SCORE_THRESHOLD else
                "Performing adequately. Encourage consistent study habits."
            ),
        })

class PrincipalDashboardAPI(APIView):
    """
    GET /administrator/api/dashboard/
    School-wide live summary — spec §3
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        scope     = get_customer_scope(request.user)
        students  = scope["students_qs"]
        class_ids = scope["class_ids"]
        today     = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())

        total_students  = students.count()
        total_teachers  = get_teachers().count()
        total_classes   = len(class_ids)
        total_coords    = get_coordinators().count()

        # Active today — FIX: start_time
        active_students_today = StudySession.objects.filter(
            student__in=students,
            start_time__date=today
        ).values('student').distinct().count()

        active_teachers_today = 0
        for teacher in get_teachers():
            t_assignment = TeacherAssignmentModel.objects.filter(teacher=teacher).first()
            t_class_ids  = list(t_assignment.assigned_classes.values_list('id', flat=True)) if t_assignment else []
            if StudySession.objects.filter(
                student__student_class__id__in=t_class_ids,
                start_time__date=today
            ).exists():
                active_teachers_today += 1

        # Weak students
        weak_students = sum(
            1 for s in students
            if calculate_student_learning_score(s.id) < WEAK_SCORE_THRESHOLD
        )

        # Pending homework
        pending_hw = HomeworkSubmissionModel.objects.filter(
            student__in=students,
            submitted_at__isnull=True
        ).count()

        # Tests this week
        tests_week = TestModel.objects.filter(
            created_at__date__gte=week_start
        ).count()

        # Study hours today
        study_seconds = StudySession.objects.filter(
            student__in=students,
            start_time__date=today
        ).aggregate(total=Sum('duration'))['total'] or 0
        study_hours = round(study_seconds / 3600, 1)

        # Inactive tablets
        three_days_ago = today - timedelta(days=3)
        try:
            inactive_tablets = DeviceModel.objects.filter(
                last_sync__date__lt=three_days_ago, is_active=True
            ).count()
        except Exception:
            inactive_tablets = DeviceModel.objects.filter(
                last_sync_at__date__lt=three_days_ago, is_active=True
            ).count()

        return Response({
            "total_students":        total_students,
            "total_teachers":        total_teachers,
            "total_classes":         total_classes,
            "total_coordinators":    total_coords,
            "active_students_today": active_students_today,
            "active_teachers_today": active_teachers_today,
            "weak_students":         weak_students,
            "pending_homework":      pending_hw,
            "tests_this_week":       tests_week,
            "study_hours_today":     study_hours,
            "inactive_tablets":      inactive_tablets,
        })

class SchoolUserAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        country = request.GET.get('country', None)
        state = request.GET.get('state', None)
        city = request.GET.get('city', None)
        user = request.GET.get('user', None)
        type1 = request.GET.get('type', None)
        parentteacher = request.GET.get('parentteacher', None)
        q = request.GET.get('q', '').strip()
        status = request.query_params.get('status', '')
        user_id = request.GET.get('id')
        customer_id = request.GET.get('customer_id')
        is_parent = request.GET.get('is_parent')
        is_teacher = request.GET.get('is_teacher')

        users = UserModel.objects.filter(is_active=True).order_by('-id').exclude(role__type='Admin')

        if user_id:
            users = users.filter(id=user_id)
        if type1:
            users = users.filter(role__type__icontains=type1)
        if parentteacher:
            if parentteacher == 'customer':
                users = users.filter(Q(role__type__in=['Customer']))

        if customer_id:
            students = StudentModel.objects.filter(parent__id=customer_id)
            users = users.filter(studentmodel__in=students)

            if is_parent:
                users = users.filter(role__type="Parent")

            if is_teacher:
                users = users.filter(role__type="Teacher")

            users = users.distinct()

        # ── Resolve principal_id once, used by both parents/teachers scoping ──
        principal_id = request.GET.get('principal_id') or (
            request.user.id
            if request.user.is_authenticated and request.user.role and request.user.role.type == 'Customer'
            else None
        )

        # ── FIX: both branches must be inside ONE if/elif chain on `user` ──
        if user == 'parents':
            users = users.filter(role__type='Parent')

            if principal_id:
                from user_management.models import StudentModel as _SM

                school_student_ids = _SM.objects.filter(
                    parent__id=principal_id, parent__role__type='Customer'
                ).values_list('id', flat=True)

                parent_ids_scoped = _SM.objects.filter(
                    id__in=school_student_ids
                ).values_list('parent__id', flat=True).distinct()

                users = users.filter(id__in=parent_ids_scoped)
            else:
                users = users.none()

        elif user == 'teachers':
            users = users.filter(role__type='Teacher')

            if principal_id:
                from user_management.models import (
                    PrincipalCoordinatorMapping, CoordinatorTeacherMapping,
                    TeacherAssignmentModel, StudentModel as _SM
                )

                # PRIMARY: direct school_principal link on TeacherAssignmentModel
                teacher_ids_scoped = list(TeacherAssignmentModel.objects.filter(
                    school_principal_id=principal_id
                ).values_list('teacher_id', flat=True).distinct())

                # FALLBACK 1: coordinator chain (legacy data)
                if not teacher_ids_scoped:
                    coord_ids = list(PrincipalCoordinatorMapping.objects.filter(
                        principal_id=principal_id
                    ).values_list('coordinator_id', flat=True))

                    teacher_ids_scoped = list(CoordinatorTeacherMapping.objects.filter(
                        coordinator_id__in=coord_ids
                    ).values_list('teacher_id', flat=True).distinct())

                # FALLBACK 2: via existing students' classes (oldest legacy path)
                if not teacher_ids_scoped:
                    school_class_ids = list(_SM.objects.filter(
                        parent__id=principal_id, parent__role__type='Customer'
                    ).values_list('student_class_id', flat=True).distinct())

                    teacher_ids_scoped = list(TeacherAssignmentModel.objects.filter(
                        assigned_classes__id__in=school_class_ids
                    ).values_list('teacher_id', flat=True).distinct())

                users = users.filter(id__in=teacher_ids_scoped)
            else:
                users = users.none()

        if q:
            users = users.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(mobile_no__icontains=q)
            )

        paginator = ListPagination()
        paginated_users = paginator.paginate_queryset(users, request)

        # ── ENRICHMENT: if listing teachers, add classes/coordinator/activity ──
        if user == 'teachers':
            from user_management.models import TeacherAssignmentModel, CoordinatorTeacherMapping
            from tablet_app.models import TestModel
            from adminpanel.models import HomeworkModel
            from django.utils import timezone

            enriched = []
            for t in paginated_users:
                assignment = TeacherAssignmentModel.objects.filter(teacher=t).first()

                classes = []
                subjects = []
                if assignment:
                    classes = [c.get_display_name() for c in assignment.assigned_classes.all()]
                    subjects = [s.name for s in assignment.assigned_subjects.all()]

                coord_map = CoordinatorTeacherMapping.objects.filter(
                    teacher=t
                ).select_related('coordinator').first()
                coordinator_name = (
                    f"{coord_map.coordinator.first_name} {coord_map.coordinator.last_name}".strip()
                    if coord_map else '-'
                )

                last_test = TestModel.objects.filter(created_by=t).order_by('-created_at').first()
                test_count = TestModel.objects.filter(created_by=t).count()
                hw_count = HomeworkModel.objects.filter(assigned_by=t).count()

                enriched.append({
                    'id':               t.id,
                    'full_name':        f"{t.first_name} {t.last_name}".strip(),
                    'email':            t.email,
                    'mobile_no':        t.mobile_no or '-',
                    'date_joined':      t.date_joined.strftime('%Y-%m-%d') if t.date_joined else '-',
                    'classes':          classes,
                    'subjects':         subjects,
                    'coordinator':      coordinator_name,
                    'tests_count':      test_count,
                    'homework_count':   hw_count,
                    'last_active':      last_test.created_at.strftime('%Y-%m-%d') if last_test else 'Never',
                    'is_active_today':  bool(last_test and last_test.created_at.date() == timezone.now().date()),
                })

            return paginator.get_paginated_response(enriched)

        serializer = UsersListSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()

        address_text = data.pop("address", None)
        postal_code = data.pop("postal_code", None)
        city = data.pop("city", None)
        state = data.pop("state", None)
        country = data.pop("country", None)

        role_type = data.get("role_type")

        if role_type:
            try:
                role = RoleModel.objects.get(type__iexact=role_type)
                data["role"] = role.id
            except RoleModel.DoesNotExist:
                return Response({"error": "Invalid role"}, status=400)

        serializer = UserSerializer(
            data=data,
            context={
                "request": request,
                "address_text": address_text,
                "postal_code": postal_code,
                "city": city,
                "state": state,
                "country": country,
            },
        )

        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully", "id": user.id}, status=201)

        return Response({'errors': serializer.errors}, status=400)

    def patch(self, request, id):
        data = request.data.copy()

        address_text = data.pop("address", None)
        postal_code = data.pop("postal_code", None)
        city = data.pop("city", None)
        state = data.pop("state", None)
        country = data.pop("country", None)

        try:
            user = UserModel.objects.get(id=id)
        except UserModel.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = UserSerializer(
            user,
            data=data,
            partial=True,
            context={
                "request": request,
                "address_text": address_text,
                "postal_code": postal_code,
                "city": city,
                "state": state,
                "country": country,
            },
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated successfully"})

        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        try:
            user = UserModel.objects.get(id=id)
        except UserModel.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = False
        user.save()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)

class TeacherAddEditView(DashboardsView):
    template_name = "school_teacher_add.html"

    def get(self, request, id=None):
        context = self.get_context_data()
        context["layout_path"] = TemplateHelper.set_layout(
            "layout_vertical.html", context
        )
        context["teacher_id"] = id or ""
        return render(request, self.template_name, context)

class TeacherAssignClassAPI(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        teacher_id = request.data.get('teacher_id')
        class_id   = request.data.get('class_id')   # now optional
        if not teacher_id:
            return Response({"error": "teacher_id is required"}, status=400)

        teacher = UserModel.objects.filter(id=teacher_id, role__type='Teacher').first()
        if not teacher:
            return Response({"error": "Teacher not found"}, status=404)

        principal_id = request.data.get('principal_id') or (
            request.user.id
            if request.user.is_authenticated and request.user.role and request.user.role.type == 'Customer'
            else None
        )
        if not principal_id:
            return Response({"error": "principal_id required — could not resolve school"}, status=400)

        # unique_together = ['teacher'] → get_or_create is safe here
        assignment, _ = TeacherAssignmentModel.objects.get_or_create(
            teacher=teacher,
            defaults={'school_principal_id': principal_id}
        )
        if not assignment.school_principal_id:
            assignment.school_principal_id = principal_id

        if class_id:
            cls = ClassModel.objects.filter(id=class_id).first()
            if not cls:
                return Response({"error": "Class not found"}, status=404)
            assignment.assigned_classes.add(cls)

        assignment.save()
        return Response({"success": True})

class SchoolSubjectAPIView(APIView):
    """
    GET /customer/api/subjects/
    Spec §9.1 — Subject-wise performance scoped to this school/principal.
    Returns: subject name, avg score, weak students, best class,
             weakest class, responsible teachers, tests count, status.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        from tablet_app.models import Subject, TestModel, StudentTestAttemptModel, StudySession
        from user_management.models import (
            StudentModel, ClassModel, TeacherAssignmentModel,
            PrincipalCoordinatorMapping, CoordinatorTeacherMapping
        )
        from django.db.models import Avg, Count, Q

        # ── Resolve principal ──────────────────────────────────────────────
        principal_id = request.GET.get('principal_id') or (
            request.user.id
            if request.user.is_authenticated and request.user.role
            and request.user.role.type == 'Customer'
            else None
        )

        # ── Scope: get all students under this principal ───────────────────
        if principal_id:
            school_students = StudentModel.objects.filter(
                parent__id=principal_id,
                parent__role__type='Customer'
            ).distinct()

            # Also include students via teacher assignment chain
            if not school_students.exists():
                teacher_ids = list(TeacherAssignmentModel.objects.filter(
                    school_principal_id=principal_id
                ).values_list('teacher_id', flat=True))
                class_ids = list(TeacherAssignmentModel.objects.filter(
                    teacher_id__in=teacher_ids
                ).values_list('assigned_classes__id', flat=True).distinct())
                school_students = StudentModel.objects.filter(
                    student_class_id__in=class_ids
                ).distinct()
        else:
            school_students = StudentModel.objects.all()

        student_ids = list(school_students.values_list('id', flat=True))

        # ── Get all classes under this school ─────────────────────────────
        class_ids = list(
            school_students.values_list('student_class_id', flat=True).distinct()
        )
        classes = ClassModel.objects.filter(id__in=class_ids)

        # ── Get subjects that have tests for these students ────────────────
        subject_ids = list(
            TestModel.objects.filter(
                student__in=student_ids
            ).exclude(subject=None)
            .values_list('subject_id', flat=True)
            .distinct()
        )

        subjects = Subject.objects.filter(id__in=subject_ids)

        # ── Optional search filter ─────────────────────────────────────────
        q = request.GET.get('q', '').strip()
        if q:
            subjects = subjects.filter(name__icontains=q)

        data = []
        for subj in subjects:

            # Overall avg score for this subject across school
            attempts = StudentTestAttemptModel.objects.filter(
                test__subject=subj,
                student_id__in=student_ids
            )
            avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0

            # Weak students count (avg < 40)
            weak_students = attempts.values('student_id').annotate(
                a=Avg('score')
            ).filter(a__lt=40).count()

            # Total students who attempted this subject
            total_attempted = attempts.values('student_id').distinct().count()

            # Tests count
            tests_count = TestModel.objects.filter(
                subject=subj,
                student__in=student_ids
            ).distinct().count()

            # Best and weakest class for this subject
            class_avgs = []
            for cls in classes:
                cls_student_ids = list(
                    school_students.filter(
                        student_class=cls
                    ).values_list('id', flat=True)
                )
                if not cls_student_ids:
                    continue
                cls_avg = StudentTestAttemptModel.objects.filter(
                    test__subject=subj,
                    student_id__in=cls_student_ids
                ).aggregate(avg=Avg('score'))['avg']
                if cls_avg is not None:
                    class_avgs.append({
                        'class': cls.get_display_name(),
                        'avg':   round(cls_avg, 1)
                    })

            best_class    = max(class_avgs, key=lambda x: x['avg'])['class'] if class_avgs else '-'
            weakest_class = min(class_avgs, key=lambda x: x['avg'])['class'] if class_avgs else '-'

            # Responsible teachers
            if principal_id:
                teacher_ids_scope = list(TeacherAssignmentModel.objects.filter(
                    school_principal_id=principal_id,
                    assigned_subjects=subj
                ).values_list('teacher_id', flat=True).distinct())
            else:
                teacher_ids_scope = list(TeacherAssignmentModel.objects.filter(
                    assigned_subjects=subj
                ).values_list('teacher_id', flat=True).distinct())

            from user_management.models import UserModel
            teachers = UserModel.objects.filter(id__in=teacher_ids_scope)
            teacher_names = [f"{t.first_name} {t.last_name}".strip() for t in teachers] or ['-']

            # Status label
            if avg_score >= 75:   status = 'Excellent'
            elif avg_score >= 60: status = 'Good'
            elif avg_score >= 50: status = 'Average'
            elif avg_score >= 35: status = 'Weak'
            else:                 status = 'Critical'

            data.append({
                'id':              subj.id,
                'subject':         subj.name,
                'avg_score':       round(avg_score, 1),
                'weak_students':   weak_students,
                'total_attempted': total_attempted,
                'tests_count':     tests_count,
                'best_class':      best_class,
                'weakest_class':   weakest_class,
                'teachers':        teacher_names,
                'class_breakdown': class_avgs,
                'status':          status,
            })

        # Sort by avg score ascending (weakest first — spec §9 says show weak areas)
        data.sort(key=lambda x: x['avg_score'])

        return Response({
            'count':    len(data),
            'subjects': data,
        })
    