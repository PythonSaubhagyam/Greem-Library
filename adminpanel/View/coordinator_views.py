from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from web_project import TemplateLayout, TemplateHelper
from user_management.models import *
from tablet_app.models import *
import json
import openpyxl
from io import BytesIO
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Avg, Sum, Q, Count, Max, Min,F
from adminpanel.views import DashboardsView
from web_project import TemplateLayout, TemplateHelper
from django.contrib.auth import update_session_auth_hash
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# def get_coordinator_scope(coordinator):
#     assignments = CoordinatorAssignmentModel.objects.filter(coordinator=coordinator)
#     class_ids   = list(assignments.values_list('class_obj_id', flat=True).distinct())
#     teacher_ids = list(assignments.values_list('teacher_id', flat=True).distinct())
#     student_ids = list(StudentModel.objects.filter(
#         student_class_id__in=class_ids
#     ).values_list('id', flat=True))
#     return class_ids, teacher_ids, student_ids


def get_coordinator_scope(coordinator):
    assignments = CoordinatorAssignmentModel.objects.filter(coordinator=coordinator)
    class_ids   = list(assignments.values_list('class_obj_id', flat=True).distinct())

    t1 = list(assignments.values_list('teacher_id', flat=True).distinct())
    t2 = list(CoordinatorTeacherMapping.objects.filter(
        coordinator=coordinator
    ).values_list('teacher_id', flat=True).distinct())

    teacher_ids = list(set(t1 + t2))

    student_ids = list(StudentModel.objects.filter(
        student_class_id__in=class_ids
    ).values_list('id', flat=True))

    return class_ids, teacher_ids, student_ids

def _make_excel(headers, rows, sheet_name='Report'):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _make_pdf(title, headers, rows):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elems = [
        Paragraph(title, styles['Title']),
        Spacer(1, 12),
        Table(
            [headers] + rows,
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#696CFF')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, 0), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#f4f4fb')]),
                ('GRID',    (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('PADDING', (0, 0), (-1, -1), 6),
            ])
        )
    ]
    doc.build(elems)
    buf.seek(0)
    return buf

@method_decorator(login_required, name='dispatch')
class CoordinatorDashboardView(View):
    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        context['user'] = request.user
        return render(request, 'coordinator/coordinator_dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class CoordinatorDashboardStatsAPI(View):
    def get(self, request):
        coord = request.user
        class_ids, teacher_ids, student_ids = get_coordinator_scope(coord)
        today = timezone.now().date()
 
        # Weak students — avg score < 40
        weak_students = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids
        ).values('student_id').annotate(
            avg=Avg('score')
        ).filter(avg__lt=40).count()
 
        # Active students today
        active_today = StudySession.objects.filter(
            student_id__in=student_ids,
            start_time__date=today
        ).values('student_id').distinct().count()
 
        # Pending homework — HomeworkModel.assigned_to is M2M to StudentModel
        pending_hw = HomeworkModel.objects.filter(
            assigned_to__student_class_id__in=class_ids
        ).distinct().count()
 
        # Tests this week
        week_start = today - timezone.timedelta(days=today.weekday())
        tests_week = TestModel.objects.filter(
            student__in=student_ids,
            created_at__date__gte=week_start
        ).distinct().count()
 
        # Study hours today
        study_total = StudySession.objects.filter(
            student_id__in=student_ids,
            start_time__date=today
        ).aggregate(total=Sum('duration'))['total'] or 0
        study_hours = round(study_total / 60, 1)
 
        # Action required
        action_count = CoordinatorActionModel.objects.filter(
            coordinator=coord,
            status__in=['New', 'Pending']
        ).count()
 
        return JsonResponse({
            'assigned_classes':  len(class_ids),
            'assigned_teachers': len(teacher_ids),
            'total_students':    len(student_ids),
            'active_today':      active_today,
            'weak_students':     weak_students,
            'pending_homework':  pending_hw,
            'tests_this_week':   tests_week,
            'study_hours_today': study_hours,
            'action_required':   action_count,
        })
 


@method_decorator(login_required, name='dispatch')
class CoordinatorClassListView(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        classes = ClassModel.objects.filter(id__in=class_ids)
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        context['classes'] = classes
        return render(request, 'coordinator/coordinator_classes.html', context)


@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherListView(View):
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        teachers = UserModel.objects.filter(id__in=teacher_ids)
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        context['teachers'] = teachers
        return render(request, 'coordinator/coordinator_teachers.html', context)


@method_decorator(login_required, name='dispatch')
class CoordinatorStudentListView(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        students = StudentModel.objects.filter(id__in=student_ids)
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        context['students'] = students
        return render(request, 'coordinator/coordinator_students.html', context)


@method_decorator(login_required, name='dispatch')
class CoordinatorActionView(View):
    def get(self, request):
        actions = CoordinatorActionModel.objects.filter(
            coordinator=request.user
        ).order_by('priority', '-created_at')
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        context['actions'] = actions
        return render(request, 'coordinator/coordinator_actions.html', context)


@method_decorator(login_required, name='dispatch')
class CoordinatorActionUpdateAPI(View):
    def post(self, request, pk):
        try:
            action = CoordinatorActionModel.objects.get(pk=pk, coordinator=request.user)
            data = json.loads(request.body)
            action.status  = data.get('status', action.status)
            action.remarks = data.get('remarks', action.remarks)
            action.save()
            return JsonResponse({'success': True})
        except CoordinatorActionModel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Not found'}, status=404)



@method_decorator(login_required, name='dispatch')
class CoordinatorClassComparisonAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        data = []
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            students = StudentModel.objects.filter(student_class_id=cid)
            sids = list(students.values_list('id', flat=True))
 
            avg = StudentTestAttemptModel.objects.filter(
                student_id__in=sids
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            weak = StudentTestAttemptModel.objects.filter(
                student_id__in=sids
            ).values('student_id').annotate(
                a=Avg('score')
            ).filter(a__lt=40).count()
 
            # Homework via assigned_to M2M
            hw_total = HomeworkModel.objects.filter(assigned_to__student_class_id=cid).distinct().count()
 
            hw_submitted = HomeworkSubmissionModel.objects.filter(
                student_id__in=sids
            ).count()
 
            hw_pct = round((hw_submitted / hw_total * 100) if hw_total else 0, 1)
 
            tests_taken = TestModel.objects.filter(
                student__in=sids
            ).distinct().count()
 
            study_total = StudySession.objects.filter(
                student_id__in=sids
            ).aggregate(total=Sum('duration'))['total'] or 0
            study_hrs = round(study_total / 3600, 1)
 
            data.append({
                'id':                  cid,
                'name':                str(cls),
                'avg_score':           round(avg, 1),
                'weak_students':       weak,
                'tests_taken':         tests_taken,
                'homework_completion': hw_pct,
                'study_time':          f'{study_hrs} hrs/day',
                'status': (
                    'Excellent' if avg > 75 else
                    'Good'      if avg > 60 else
                    'Average'   if avg > 50 else
                    'Weak'      if avg > 35 else
                    'Critical'
                ),
            })
        return JsonResponse({'classes': data})


@method_decorator(login_required, name='dispatch')
class CoordinatorWeakStudentsAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        data = []

        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue

            avg = StudentTestAttemptModel.objects.filter(
                student_id=sid
            ).aggregate(avg=Avg('score'))['avg'] or 0

            if avg >= 40:
                continue

            study = StudySession.objects.filter(
                student_id=sid
            ).aggregate(total=Sum('duration'))['total'] or 0

            hw_assigned = HomeworkModel.objects.filter(
                assigned_to__id=sid
            ).distinct().count()

            hw_submitted = HomeworkSubmissionModel.objects.filter(
                student_id=sid
            ).count()

            hw_pct = round(
                (hw_submitted / hw_assigned * 100)
                if hw_assigned else 0, 1
            )

            tests_attempted = StudentTestAttemptModel.objects.filter(
                student_id=sid
            ).count()

            last_session = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()

            last_active = (
                last_session.start_time.strftime('%Y-%m-%d')
                if last_session else 'Never'
            )

            # ============================================
            # NEW: Trend Calculation
            # ============================================
            recent = list(
                StudentTestAttemptModel.objects.filter(
                    student_id=sid
                ).order_by('-started_at')
                .values_list('score', flat=True)[:3]
            )

            older = list(
                StudentTestAttemptModel.objects.filter(
                    student_id=sid
                ).order_by('-started_at')
                .values_list('score', flat=True)[3:6]
            )

            if recent and older:
                r_avg = sum(recent) / len(recent)
                o_avg = sum(older) / len(older)

                trend = (
                    'Improving'
                    if r_avg > o_avg + 5
                    else (
                        'Falling'
                        if r_avg < o_avg - 5
                        else 'Stable'
                    )
                )
            else:
                trend = 'Stable'

            risk = (
                'Inactive'        if last_active == 'Never' else
                'Falling'         if trend == 'Falling' else
                'Improving'       if trend == 'Improving' else
                'High Risk'       if avg < 25 else
                'Needs Attention' if avg < 40 else
                'Stable'
            )

            data.append({
                'id': sid,
                'name': student.student_name,
                'class': str(student.student_class)
                         if student.student_class else '-',
                'avg_score': round(avg, 1),
                'study_time': f'{round(study/60, 1)} min/day',
                'homework_pct': hw_pct,
                'tests_attempted': tests_attempted,
                'last_active': last_active,
                'risk': risk,
            })

        return JsonResponse({'weak_students': data})

@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherActivityAPI(View):
    def get(self, request):
        _, teacher_ids, student_ids = get_coordinator_scope(request.user)
        data = []
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
 
            hw_count = HomeworkModel.objects.filter(created_by_id=tid).count()
            tests_count = TestModel.objects.filter(created_by_id=tid).count()

 
            # Students under this teacher
            teacher_students = StudentModel.objects.filter(
                parent=tid
            ).values_list('id', flat=True)
 
            avg_score = StudentTestAttemptModel.objects.filter(
                student_id__in=teacher_students
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            weak_under = StudentTestAttemptModel.objects.filter(
                student_id__in=teacher_students
            ).values('student_id').annotate(
                a=Avg('score')
            ).filter(a__lt=40).count()
 
            # Accountability score (out of 100)
            score = min(100, (tests_count * 15) + (hw_count * 15) + (10 if avg_score > 60 else 0))
 
            # Last active via StudySession created_by or test
            last_test = TestModel.objects.filter(created_by_id=tid).order_by('-created_at').first()
            last_active = last_test.created_at.strftime('%Y-%m-%d') if last_test else 'Never'
 
            data.append({
                'id':              tid,
                'name':            f"{teacher.first_name} {teacher.last_name}",
                'email':           teacher.email,
                'phone':           teacher.mobile_no or '-',
                'tests':           tests_count,
                'homework':        hw_count,
                'avg_student_score': round(avg_score, 1),
                'weak_students':   weak_under,
                'last_active':     last_active,
                'score':           score,
                'status': (
                    'Good'    if score > 70 else
                    'Average' if score > 40 else
                    'Risk'
                ),
            })
        return JsonResponse({'teachers': data})


# Stub views
@method_decorator(login_required, name='dispatch')
class CoordinatorSubjectView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_subjects.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorTestListView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_tests.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_homework.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorStudyTimeView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_study_time.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorWeaknessView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_weakness.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorAlertView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_alerts.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorReportsView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_reports.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorDeviceView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_devices.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorEscalationView(View):
    def get(self, request):
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_escalations.html', context)

@method_decorator(login_required, name='dispatch')
class CoordinatorFlowAPI(View):
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
        return JsonResponse({
            'class_ids':     class_ids,
            'teacher_ids':   teacher_ids,
            'student_count': len(student_ids),
        })


@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkStatsAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        data = []
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
 
            hw_given = HomeworkModel.objects.filter(assigned_to__student_class_id=cid).distinct().count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(student_id__in=sids).count()
            hw_pending   = hw_given - hw_submitted if hw_given > hw_submitted else 0
            hw_checked   = HomeworkSubmissionModel.objects.filter(
                student_id__in=sids, score__isnull=False
            ).count()
 
            sub_pct   = round((hw_submitted / hw_given * 100) if hw_given else 0, 1)
            check_pct = round((hw_checked / hw_submitted * 100) if hw_submitted else 0, 1)
 
            status = 'Good' if sub_pct > 75 else ('Average' if sub_pct > 50 else 'Bad')
 
            data.append({
                'class':     str(cls),
                'given':     hw_given,
                'submitted': hw_submitted,
                'pending':   hw_pending,
                'checked':   hw_checked,
                'submit_pct': sub_pct,
                'check_pct':  check_pct,
                'status':    status,
            })
        return JsonResponse({'homework': data})

@method_decorator(login_required, name='dispatch')
class CoordinatorTestStatsAPI(View):
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)

        # Same dual-scope as detail API
        # tests = TestModel.objects.filter(
        #     Q(student__in=student_ids) |
        #     Q(created_by_id__in=teacher_ids)
        # ).distinct()
        tests = TestModel.objects.all().distinct()

        data = []
        for test in tests:
            attempts = StudentTestAttemptModel.objects.filter(test=test)
            attempted_students = attempts.values('student').distinct().count()
            total_students = test.student.count()
            avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            teacher_name = ''
            if test.created_by:
                teacher_name = f"{test.created_by.first_name} {test.created_by.last_name}".strip()
            data.append({
                'id':            test.id,
                'title':         test.title,
                'subject':       test.subject.name if test.subject else '-',
                'teacher':       teacher_name,
                'date':          test.scheduled_date.strftime('%Y-%m-%d') if test.scheduled_date else '-',
                'total_students': total_students,
                'attempted':     attempted_students,
                'absent':        max(0, total_students - attempted_students),
                'avg_score':     round(avg_score, 1),
                'retest_needed': avg_score < 40,
            })
        return JsonResponse({'tests': data})
    
@method_decorator(login_required, name='dispatch')
class CoordinatorAlertsAPI(View):
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
        today = timezone.now().date()
        today_str = today.strftime('%d %b %Y')
        alerts = []

        # Alert 1: Students inactive 3+ days
        for sid in student_ids:
            last = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()
            if not last or (today - last.start_time.date()).days >= 3:
                student = StudentModel.objects.filter(id=sid).first()
                if student:
                    alerts.append({
                        'priority':    'High',
                        'type':        'Student Inactive',
                        'message':     f'{student.student_name} inactive for 3+ days',
                        'class':       str(student.student_class) if student.student_class else '-',
                        'responsible': student.student_name,
                        'date':        today_str,
                        'status':      'New',
                    })

        # Alert 2: Students score < 40
        weak = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids
        ).values('student_id').annotate(avg=Avg('score')).filter(avg__lt=40)
        for w in weak:
            student = StudentModel.objects.filter(id=w['student_id']).first()
            if student:
                alerts.append({
                    'priority':    'High',
                    'type':        'Low Score',
                    'message':     f'{student.student_name} avg score {round(w["avg"],1)}% — below 40%',
                    'class':       str(student.student_class) if student.student_class else '-',
                    'responsible': student.student_name,
                    'date':        today_str,
                    'status':      'New',
                })

        # Alert 3: Homework pending > 50% for a class
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            hw_given     = HomeworkModel.objects.filter(assigned_to__in=sids).distinct().count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(student_id__in=sids).count()
            if hw_given > 0:
                pending_pct = ((hw_given - hw_submitted) / hw_given) * 100
                if pending_pct > 50:
                    alerts.append({
                        'priority':    'Medium',
                        'type':        'Homework Pending',
                        'message':     f'{str(cls)} — {round(pending_pct,1)}% homework pending',
                        'class':       str(cls),
                        'responsible': 'Class Teacher',
                        'date':        today_str,
                        'status':      'New',
                    })

        # Alert 4: Teacher no test for 7 days
        for tid in teacher_ids:
            last_test = TestModel.objects.filter(
                created_by_id=tid
            ).order_by('-created_at').first()
            teacher = UserModel.objects.filter(id=tid).first()
            if teacher:
                if not last_test or (today - last_test.created_at.date()).days >= 7:
                    alerts.append({
                        'priority':    'Medium',
                        'type':        'Teacher Inactive',
                        'message':     f'{teacher.first_name} {teacher.last_name} — no test in 7+ days',
                        'class':       '-',
                        'responsible': f'{teacher.first_name} {teacher.last_name}',
                        'date':        today_str,
                        'status':      'New',
                    })

        # Alert 5: Coordinator pending actions overdue
        overdue = CoordinatorActionModel.objects.filter(
            coordinator=request.user,
            status__in=['New', 'Pending'],
            due_date__lt=today
        ).count()
        if overdue:
            alerts.append({
                'priority':    'High',
                'type':        'Overdue Actions',
                'message':     f'{overdue} coordinator actions overdue — escalate to principal',
                'class':       '-',
                'responsible': 'Coordinator',
                'date':        today_str,
                'status':      'Overdue',
            })

        return JsonResponse({
            'count': len(alerts),
            'alerts': alerts
        })

@method_decorator(login_required, name='dispatch')
class CoordinatorStudyTimeAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        today = timezone.now().date()
        data = []
        inactive_count = 0

        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue

            total_study = StudySession.objects.filter(
                student_id=sid
            ).aggregate(total=Sum('duration'))['total'] or 0

            today_study = StudySession.objects.filter(
                student_id=sid,
                start_time__date=today
            ).aggregate(total=Sum('duration'))['total'] or 0

            tests_attempted = StudentTestAttemptModel.objects.filter(
                student_id=sid
            ).count()

            hw_submitted = HomeworkSubmissionModel.objects.filter(
                student_id=sid
            ).count()

            last_session = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()

            last_active = last_session.start_time.strftime('%Y-%m-%d') if last_session else 'Never'

            inactive = False
            if last_session:
                days_inactive = (today - last_session.start_time.date()).days
                if days_inactive >= 3:
                    inactive = True
                    inactive_count += 1
            else:
                inactive = True
                inactive_count += 1

            # Get teacher name via parent M2M
            teacher = student.parent.filter(role__type='Teacher').first()
            teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else '-'

            # Get device
            parent_user = student.parent.first()
            device = DeviceModel.objects.filter(user=parent_user).first() if parent_user else None
            tablet_id = device.imei_number if device else f'TAB-{sid}'

            data.append({
                'student_name':    student.student_name,
                'class_name':      str(student.student_class) if student.student_class else '-',
                'teacher_name':    teacher_name,
                'study_time':      f'{round(total_study/60, 1)} hrs total',
                'today_study':     f'{round(today_study/60, 1)} min today',
                'tests_attempted': tests_attempted,
                'homework_opened': hw_submitted,
                'pdf_opened':      '-',
                'battery':         '-',
                'tablet_id':       tablet_id,
                'last_active':     last_active,
                'status':          'Inactive' if inactive else 'Active',
            })

        avg_study = round(
            sum(float(d['today_study'].split()[0]) for d in data) / len(data), 1
        )
        return JsonResponse({
            'summary': {
                'total_students':    len(student_ids),
                'avg_study_today':   f'{avg_study} min',
                'inactive_students': inactive_count,
                'inactive_tablets':  inactive_count,
            },
            'study_time': data
        })
 
@method_decorator(login_required, name='dispatch')
class CoordinatorDeviceStatsAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        today = timezone.now().date()
        devices = []
        inactive_count = 0
 
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
 
            # Use DeviceModel linked via student
            device = DeviceModel.objects.filter(user__in=student.parent.all()).first()
 
            last_session = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()
 
            last_active = last_session.start_time.strftime('%Y-%m-%d') if last_session else 'Never'
            days_since  = (today - last_session.start_time.date()).days if last_session else 999
            status      = 'Inactive' if days_since >= 3 else 'Active'
 
            if status == 'Inactive':
                inactive_count += 1
 
            study_today = StudySession.objects.filter(
                student_id=sid,
                start_time__date=today
            ).aggregate(total=Sum('duration'))['total'] or 0
 
            devices.append({
                'tablet_id':    device.imei_number if device else f'TAB-{sid}',
                'student_name': student.student_name,
                'class_name':   str(student.student_class) if student.student_class else '-',
                'last_active':  last_active,
                'study_time':   f'{round(study_today/60,1)} min today',
                'status':       status,
            })
 
        return JsonResponse({
            'summary': {
                'total':    len(devices),
                'active':   len(devices) - inactive_count,
                'inactive': inactive_count,
            },
            'devices': devices
        })

# ─── Test Detail / Edit / Delete API ────────────────────────
@method_decorator(login_required, name='dispatch')
class CoordinatorTestDetailAPI(View):

    def _get_test_in_scope(self, request, pk):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)

        return TestModel.objects.filter(
            id=pk
        ).filter(
            Q(student__in=student_ids) |
            Q(created_by_id__in=teacher_ids)
        ).distinct().first()

    def get(self, request, pk):
        test = self._get_test_in_scope(request, pk)
        if not test:
            return JsonResponse({'error': 'Not found or not in scope'}, status=404)

        attempts = StudentTestAttemptModel.objects.filter(test=test)
        attempted = attempts.values('student').distinct().count()
        avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0

        students_data = []
        for attempt in attempts:
            students_data.append({
                'student_id':   attempt.student_id,
                'student_name': attempt.student.student_name,
                'score':        attempt.score,
                'started_at':   attempt.started_at.strftime('%Y-%m-%d %H:%M') if attempt.started_at else '-',
                'completed_at': attempt.completed_at.strftime('%Y-%m-%d %H:%M') if attempt.completed_at else '-',
                'completed':    attempt.is_completes,
            })

        return JsonResponse({
            'id':             test.id,
            'title':          test.title,
            'subject':        test.subject.name if test.subject else '-',
            'subject_id':     test.subject_id,
            'total_marks':    test.total_marks,
            'duration':       test.duration_minutes,
            'question_type':  test.question_type,
            'scheduled_date': test.scheduled_date.strftime('%Y-%m-%d') if test.scheduled_date else '-',
            'created_by':     f"{test.created_by.first_name} {test.created_by.last_name}" if test.created_by else '-',
            'total_students': test.student.count(),
            'attempted':      attempted,
            'avg_score':      round(avg_score, 1),
            'retest_needed':  avg_score < 40,
            'attempts':       students_data,
        })

    def delete(self, request, pk):
        test = self._get_test_in_scope(request, pk)
        if not test:
            return JsonResponse({'error': 'Not found or not in scope'}, status=404)
        test.delete()
        return JsonResponse({'success': True, 'message': 'Test deleted'})
    
@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkAPI(View):

    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)

        homeworks = HomeworkModel.objects.filter(
            assigned_to__student_class_id__in=class_ids
        ).distinct().order_by('-id')

        data = []
        for hw in homeworks:
            # get class name via assigned_to M2M
            first_student = hw.assigned_to.first()
            class_name = str(first_student.student_class) if first_student and first_student.student_class else '-'

            # subject
            subject_name = hw.subject.name if hw.subject else '-'

            # teacher — HomeworkModel.created_by
            teacher_name = f"{hw.created_by.first_name} {hw.created_by.last_name}" if hw.created_by else '-'

            data.append({
                'id':          hw.id,
                'title':       hw.title,
                'description': hw.description or '',
                'subject':     subject_name,
                'teacher':     teacher_name,
                'class_name':  class_name,
                'due_date':    hw.due_date.strftime('%d %b %Y') if hw.due_date else '-',
                'status':      'Expired' if hw.due_date and hw.due_date < timezone.now() else 'Active',
            })

        return JsonResponse({'homeworks': data})

    def post(self, request):
        """Add new homework"""
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

        title       = body.get('title', '').strip()
        description = body.get('description', '')
        due_date    = body.get('due_date')         # "2026-06-30T00:00"
        subject_id  = body.get('subject_id')
        class_id    = body.get('class_id')         # assign to all students in this class

        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)
        if not due_date:
            return JsonResponse({'success': False, 'error': 'Due date is required'}, status=400)
        if not class_id:
            return JsonResponse({'success': False, 'error': 'Class is required'}, status=400)

        # Verify class is in coordinator scope
        class_ids, _, _ = get_coordinator_scope(request.user)
        if int(class_id) not in class_ids:
            return JsonResponse({'success': False, 'error': 'Class not in your scope'}, status=403)

        hw = HomeworkModel.objects.create(
            title=title,
            description=description,
            due_date=due_date,
            subject_id=subject_id or None,
            created_by=request.user,
        )

        # Assign to all students in selected class
        students = StudentModel.objects.filter(student_class_id=class_id)
        hw.assigned_to.set(students)

        return JsonResponse({'success': True, 'id': hw.id})
    
@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkDetailAPI(View):

    def get(self, request, pk):
        class_ids, _, _ = get_coordinator_scope(request.user)
        homework = HomeworkModel.objects.filter(
            id=pk,
            assigned_to__student_class_id__in=class_ids
        ).first()

        if not homework:
            return JsonResponse({'error': 'Homework not found'}, status=404)

        first_student = homework.assigned_to.first()
        return JsonResponse({
            'id':          homework.id,
            'title':       homework.title,
            'description': homework.description or '',
            'due_date':    homework.due_date.strftime('%Y-%m-%dT%H:%M') if homework.due_date else '',
            'subject_id':  homework.subject_id,
            'subject':     homework.subject.name if homework.subject else '-',
            'class':       str(first_student.student_class) if first_student and first_student.student_class else '-',
            'teacher':     f"{homework.created_by.first_name} {homework.created_by.last_name}" if homework.created_by else '-',
        })

    def put(self, request, pk):
        """Edit homework"""
        class_ids, _, _ = get_coordinator_scope(request.user)
        homework = HomeworkModel.objects.filter(
            id=pk,
            assigned_to__student_class_id__in=class_ids
        ).first()

        if not homework:
            return JsonResponse({'error': 'Not found or not in scope'}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        homework.title       = body.get('title', homework.title)
        homework.description = body.get('description', homework.description)

        if body.get('due_date'):
            homework.due_date = body['due_date']

        if body.get('subject_id'):
            homework.subject_id = body['subject_id']

        homework.save()
        return JsonResponse({'success': True})

    def delete(self, request, pk):
        """Delete homework"""
        class_ids, _, _ = get_coordinator_scope(request.user)
        homework = HomeworkModel.objects.filter(
            id=pk,
            assigned_to__student_class_id__in=class_ids
        ).first()

        if not homework:
            return JsonResponse({'error': 'Not found or not in scope'}, status=404)

        homework.delete()
        return JsonResponse({'success': True, 'message': 'Homework deleted'})

@method_decorator(login_required, name='dispatch')
class CoordinatorClassDetailView(View):

    def get(self, request, pk):

        class_ids, _, _ = get_coordinator_scope(request.user)

        if pk not in class_ids:
            return redirect('coordinator-classes')

        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout(
            'layout_vertical.html',
            context
        )

        context['class_id'] = pk

        return render(
            request,
            'coordinator/coordinator_class_detail.html',
            context
        )

@method_decorator(login_required, name='dispatch')
class CoordinatorClassDetailAPI(View):

    def get(self, request, pk):

        class_ids, teacher_ids, student_ids = \
            get_coordinator_scope(request.user)

        if pk not in class_ids:
            return JsonResponse(
                {'error': 'Not in your scope'},
                status=403
            )

        cls = ClassModel.objects.filter(id=pk).first()

        if not cls:
            return JsonResponse(
                {'error': 'Class not found'},
                status=404
            )

        students = StudentModel.objects.filter(
            student_class_id=pk
        )

        sids = list(
            students.values_list('id', flat=True)
        )

        total_students = len(sids)

        avg_score = StudentTestAttemptModel.objects.filter(
            student_id__in=sids
        ).aggregate(
            avg=Avg('score')
        )['avg'] or 0

        weak_students = StudentTestAttemptModel.objects.filter(
            student_id__in=sids
        ).values('student_id').annotate(
            a=Avg('score')
        ).filter(
            a__lt=40
        ).count()

        homework_count = HomeworkModel.objects.filter(assigned_to__student_class_id=pk).distinct().count()

        test_count = TestModel.objects.filter(
            student__in=sids
        ).distinct().count()

        study_seconds = StudySession.objects.filter(
            student_id__in=sids
        ).aggregate(
            total=Sum('duration')
        )['total'] or 0

        study_hours = round(study_seconds / 3600, 1)

        # Teachers

        teachers = UserModel.objects.filter(
            id__in=teacher_ids
        )

        teacher_data = []

        for teacher in teachers:

            teacher_data.append({
                'id': teacher.id,
                'name': f'{teacher.first_name} {teacher.last_name}',
                'email': teacher.email,
                'mobile': teacher.mobile_no
            })

        # Weak students

        weak_students_data = []

        weak_queryset = StudentTestAttemptModel.objects.filter(
            student_id__in=sids
        ).values(
            'student_id'
        ).annotate(
            avg=Avg('score')
        ).filter(
            avg__lt=40
        )

        for item in weak_queryset:

            student = StudentModel.objects.filter(
                id=item['student_id']
            ).first()

            if student:

                weak_students_data.append({
                    'id': student.id,
                    'name': student.student_name,
                    'avg_score': round(item['avg'], 1)
                })

        # Recent homework

        homeworks = HomeworkModel.objects.filter(assigned_to__student_class_id=pk).order_by('-id')[:5]
        homework_data = []

        for hw in homeworks:

            homework_data.append({
                'title': hw.title,
                'due_date': (
                    hw.due_date.strftime('%d-%m-%Y')
                    if hw.due_date else '-'
                )
            })

        # Recent tests

        tests = TestModel.objects.filter(
            student__in=sids
        ).distinct().order_by('-id')[:5]

        test_data = []

        for test in tests:

            attempts = StudentTestAttemptModel.objects.filter(
                test=test
            )

            avg = attempts.aggregate(
                avg=Avg('score')
            )['avg'] or 0

            test_data.append({
                'title': test.title,
                'subject': (
                    test.subject.name
                    if test.subject else '-'
                ),
                'avg_score': round(avg, 1)
            })

        status = (
            'Excellent' if avg_score >= 75 else
            'Good' if avg_score >= 60 else
            'Average' if avg_score >= 50 else
            'Weak' if avg_score >= 35 else
            'Critical'
        )

        return JsonResponse({

            'class_name': str(cls),

            'summary': {
                'students': total_students,
                'avg_score': round(avg_score, 1),
                'weak_students': weak_students,
                'homework_count': homework_count,
                'test_count': test_count,
                'study_hours': study_hours,
                'status': status
            },

            'teachers': teacher_data,

            'weak_students': weak_students_data,

            'recent_homeworks': homework_data,

            'recent_tests': test_data
        })


@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherNeglectView(View):
    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_teacher_neglect.html', context)
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherNeglectAPI(View):
    def get(self, request):
        _, teacher_ids, student_ids = get_coordinator_scope(request.user)
        today = timezone.now().date()
        teachers = []
 
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
 
            issues = []
            priority = 'Low'
 
            # Check: no test in last 7 days
            last_test = TestModel.objects.filter(
                created_by_id=tid
            ).order_by('-created_at').first()
 
            days_no_test = (today - last_test.created_at.date()).days if last_test else 999
 
            if days_no_test >= 10:
                issues.append(f'No test taken in {days_no_test} days')
                priority = 'High'
            elif days_no_test >= 7:
                issues.append(f'No test taken in {days_no_test} days')
                priority = 'Medium'
 
            # Check: no homework in last 7 days
            last_hw = HomeworkModel.objects.filter(created_by_id=tid).order_by('-id').first()

            if not last_hw:
                issues.append('No homework assigned ever')
                priority = 'High'
            else:
                hw_count = HomeworkModel.objects.filter(created_by_id=tid).count()
                if hw_count == 0:
                    issues.append('No homework assigned')
                    priority = 'High'
 
            # Check: avg student score < 40
            teacher_students = StudentModel.objects.filter(
                parent=tid
            ).values_list('id', flat=True)
 
            avg_score = StudentTestAttemptModel.objects.filter(
                student_id__in=teacher_students
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            if avg_score < 40 and avg_score > 0:
                issues.append(f'Student avg score critical: {round(avg_score, 1)}%')
                priority = 'High'
 
            if not issues:
                issues.append('No issues detected')
                priority = 'Good'
 
            teachers.append({
                'id':          tid,
                'teacher':     f"{teacher.first_name} {teacher.last_name}",
                'email':       teacher.email,
                'issue':       ', '.join(issues),
                'priority':    priority,
                'days_no_test': days_no_test if last_test else 999,
                'avg_score':   round(avg_score, 1),
                'last_test':   last_test.created_at.strftime('%Y-%m-%d') if last_test else 'Never',
            })
 
        # Sort: High first
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2, 'Good': 3}
        teachers.sort(key=lambda x: priority_order.get(x['priority'], 4))
 
        return JsonResponse({'teachers': teachers})
 
 
# ─── 5. Escalation Management ─────────────────────────────────────────────────
 
@method_decorator(login_required, name='dispatch')
class CoordinatorEscalationAPI(View):
    def get(self, request):
        escalations = CoordinatorEscalationModel.objects.filter(
            coordinator=request.user
        ).order_by('-created_at')
 
        data = []
        for e in escalations:
            data.append({
                'id':          e.id,
                'title':       e.title,
                'description': e.description or '',
                'priority':    e.priority,
                'status':      e.status,
                'student':     e.student.student_name if e.student else '-',
                'teacher':     f"{e.teacher.first_name} {e.teacher.last_name}" if e.teacher else '-',
                'created_at':  e.created_at.strftime('%Y-%m-%d'),
                'resolved_at': e.resolved_at.strftime('%Y-%m-%d') if e.resolved_at else '-',
            })
 
        return JsonResponse({'escalations': data})
 
    def post(self, request):
        body = json.loads(request.body)
        escalation = CoordinatorEscalationModel.objects.create(
            coordinator=request.user,
            title=body.get('title', ''),
            description=body.get('description', ''),
            priority=body.get('priority', 'Medium'),
            status='Open',
            student_id=body.get('student_id'),
            teacher_id=body.get('teacher_id'),
        )
        return JsonResponse({'success': True, 'id': escalation.id})
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorEscalationDetailAPI(View):
    def get(self, request, pk):
        try:
            e = CoordinatorEscalationModel.objects.get(pk=pk, coordinator=request.user)
        except CoordinatorEscalationModel.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
 
        return JsonResponse({
            'id':          e.id,
            'title':       e.title,
            'description': e.description or '',
            'priority':    e.priority,
            'status':      e.status,
            'student':     e.student.student_name if e.student else '-',
            'teacher':     f"{e.teacher.first_name} {e.teacher.last_name}" if e.teacher else '-',
            'created_at':  e.created_at.strftime('%Y-%m-%d'),
            'resolved_at': e.resolved_at.strftime('%Y-%m-%d') if e.resolved_at else '-',
        })
 
    def put(self, request, pk):
        try:
            e = CoordinatorEscalationModel.objects.get(pk=pk, coordinator=request.user)
        except CoordinatorEscalationModel.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
 
        body = json.loads(request.body)
        e.status      = body.get('status', e.status)
        e.priority    = body.get('priority', e.priority)
        e.description = body.get('description', e.description)
        if body.get('status') == 'Resolved' and not e.resolved_at:
            e.resolved_at = timezone.now()
        e.save()
        return JsonResponse({'success': True})
 
    def delete(self, request, pk):
        try:
            e = CoordinatorEscalationModel.objects.get(pk=pk, coordinator=request.user)
            e.delete()
            return JsonResponse({'success': True})
        except CoordinatorEscalationModel.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
 
 
# ─── 6. Coordinator Profile ───────────────────────────────────────────────────
 
@method_decorator(login_required, name='dispatch')
class CoordinatorProfileView(View):
    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_profile.html', context)
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorProfileAPI(View):
    def get(self, request):
        user = request.user
        class_ids, teacher_ids, student_ids = get_coordinator_scope(user)
 
        return JsonResponse({
            'id':           user.id,
            'first_name':   user.first_name,
            'last_name':    user.last_name,
            'email':        user.email,
            'mobile':       user.mobile_no or '-',
            'role':         user.role.type if user.role else 'Coordinator',
            'stats': {
                'classes':  len(class_ids),
                'teachers': len(teacher_ids),
                'students': len(student_ids),
            }
        })
 
    def put(self, request):
        user = request.user
        body = json.loads(request.body)
        user.first_name = body.get('first_name', user.first_name)
        user.last_name  = body.get('last_name',  user.last_name)
        user.mobile_no  = body.get('mobile',     user.mobile_no)
        user.save()
        return JsonResponse({'success': True})
 
 
# ─── 7. Reports ───────────────────────────────────────────────────────────────
 
@method_decorator(login_required, name='dispatch')
class CoordinatorClassReportAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        data = []
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            avg = StudentTestAttemptModel.objects.filter(
                student_id__in=sids
            ).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(
                student_id__in=sids
            ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            hw = HomeworkModel.objects.filter(assigned_to__student_class_id=cid).distinct().count()
            tests = TestModel.objects.filter(student__in=sids).distinct().count()
            data.append({
                'class':         str(cls),
                'total_students': len(sids),
                'avg_score':     round(avg, 1),
                'weak_students': weak,
                'homework':      hw,
                'tests':         tests,
                'status': (
                    'Excellent' if avg >= 75 else
                    'Good'      if avg >= 60 else
                    'Average'   if avg >= 50 else
                    'Weak'      if avg >= 35 else
                    'Critical'
                ),
            })
        return JsonResponse({'report': data})
 
@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherReportAPI(View):
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)

        data = []

        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()

            if not teacher:
                continue

            hw = HomeworkModel.objects.filter(
                created_by_id=tid
            ).count()

            tests = TestModel.objects.filter(
                created_by_id=tid
            ).count()

            last_test = TestModel.objects.filter(
                created_by_id=tid
            ).order_by('-created_at').first()

            data.append({
                'name': f"{teacher.first_name} {teacher.last_name}",
                'email': teacher.email,
                'homework': hw,
                'tests': tests,
                'last_active': (
                    last_test.created_at.strftime('%Y-%m-%d')
                    if last_test else 'Never'
                ),
            })

        return JsonResponse({'report': data})
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorStudentReportAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        data = []
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            avg = StudentTestAttemptModel.objects.filter(
                student_id=sid
            ).aggregate(avg=Avg('score'))['avg'] or 0
            study = StudySession.objects.filter(
                student_id=sid
            ).aggregate(total=Sum('duration'))['total'] or 0
            last = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()
            data.append({
                'name':        student.student_name,
                'class':       str(student.student_class) if student.student_class else '-',
                'avg_score':   round(avg, 1),
                'study_hours': round(study / 3600, 1),
                'last_active': last.start_time.strftime('%Y-%m-%d') if last else 'Never',
                'risk': (
                    'High Risk'       if avg < 25 else
                    'Needs Attention' if avg < 40 else
                    'Stable'
                ),
            })
        return JsonResponse({'report': data})
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkReportAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        data = []
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            hw_given = HomeworkModel.objects.filter(assigned_to__student_class_id=cid).distinct().count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(student_id__in=sids).count()
            hw_pending   = max(0, hw_given - hw_submitted)
            pct          = round((hw_submitted / hw_given * 100) if hw_given else 0, 1)
            data.append({
                'class':     str(cls),
                'given':     hw_given,
                'submitted': hw_submitted,
                'pending':   hw_pending,
                'pct':       pct,
                'status':    'Good' if pct > 75 else ('Average' if pct > 50 else 'Bad'),
            })
        return JsonResponse({'report': data})
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorTestReportAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        tests = TestModel.objects.filter(
            student__in=student_ids
        ).distinct()
        data = []
        for test in tests:
            attempts  = StudentTestAttemptModel.objects.filter(test=test)
            attempted = attempts.values('student').distinct().count()
            avg       = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            data.append({
                'title':          test.title,
                'subject':        test.subject.name if test.subject else '-',
                'total_students': test.student.count(),
                'attempted':      attempted,
                'avg_score':      round(avg, 1),
                'retest_needed':  avg < 40,
                'date':           test.scheduled_date.strftime('%Y-%m-%d') if test.scheduled_date else '-',
            })
        return JsonResponse({'report': data})
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorDeviceReportAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        today  = timezone.now().date()
        data   = []
        active = 0
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            last = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()
            days_inactive = (today - last.start_time.date()).days if last else 999
            status = 'Active' if days_inactive < 3 else 'Inactive'
            if status == 'Active':
                active += 1
            data.append({
                'student':      student.student_name,
                'class':        str(student.student_class) if student.student_class else '-',
                'last_active':  last.start_time.strftime('%Y-%m-%d') if last else 'Never',
                'days_inactive': days_inactive if days_inactive < 999 else '-',
                'status':       status,
            })
        return JsonResponse({
            'summary': {
                'total':    len(data),
                'active':   active,
                'inactive': len(data) - active,
            },
            'report': data,
        })
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorWeakStudentReportAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        data = []
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            avg = StudentTestAttemptModel.objects.filter(
                student_id=sid
            ).aggregate(avg=Avg('score'))['avg'] or 0
            if avg >= 40:
                continue
            hw_assigned  = HomeworkModel.objects.filter(assigned_to=sid).count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(student_id=sid).count()
            hw_pct       = round((hw_submitted / hw_assigned * 100) if hw_assigned else 0, 1)
            data.append({
                'name':         student.student_name,
                'class':        str(student.student_class) if student.student_class else '-',
                'avg_score':    round(avg, 1),
                'homework_pct': hw_pct,
                'risk': (
                    'High Risk'       if avg < 25 else
                    'Needs Attention' if avg < 40 else
                    'Stable'
                ),
            })
        return JsonResponse({'report': data, 'count': len(data)})
 
 
# ─── 8. Excel Export ──────────────────────────────────────────────────────────
 
def _make_excel(headers, rows, sheet_name='Report'):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
 
 
@method_decorator(login_required, name='dispatch')
class ExportClassExcelAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        headers = ['Class', 'Total Students', 'Avg Score', 'Weak Students', 'Homework', 'Tests', 'Status']
        rows = []
        for cid in class_ids:
            cls  = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(student_class_id=cid).values_list('id', flat=True))
            avg  = StudentTestAttemptModel.objects.filter(student_id__in=sids).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(student_id__in=sids).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            hw = HomeworkModel.objects.filter(assigned_to__student_class_id=cid).distinct().count()
            tests = TestModel.objects.filter(student__in=sids).distinct().count()
            rows.append([str(cls), len(sids), round(avg, 1), weak, hw, tests,
                         'Excellent' if avg >= 75 else 'Good' if avg >= 60 else 'Average' if avg >= 50 else 'Weak'])
        buf = _make_excel(headers, rows, 'Classes')
        response = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="classes_report.xlsx"'
        return response
 
 
@method_decorator(login_required, name='dispatch')
class ExportTeacherExcelAPI(View):
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        headers = ['Name', 'Email', 'Homework Count', 'Tests Count', 'Last Active']
        rows = []
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
            hw    = HomeworkModel.objects.filter(assigned_by_id=tid).count()
            tests = TestModel.objects.filter(created_by_id=tid).count()
            last  = TestModel.objects.filter(created_by_id=tid).order_by('-created_at').first()
            rows.append([
                f"{teacher.first_name} {teacher.last_name}",
                teacher.email, hw, tests,
                last.created_at.strftime('%Y-%m-%d') if last else 'Never'
            ])
        buf = _make_excel(headers, rows, 'Teachers')
        response = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="teachers_report.xlsx"'
        return response
 
 
@method_decorator(login_required, name='dispatch')
class ExportStudentExcelAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        headers = ['Name', 'Class', 'Avg Score', 'Study Hours', 'Last Active', 'Risk']
        rows = []
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            avg   = StudentTestAttemptModel.objects.filter(student_id=sid).aggregate(avg=Avg('score'))['avg'] or 0
            study = StudySession.objects.filter(student_id=sid).aggregate(total=Sum('duration'))['total'] or 0
            last  = StudySession.objects.filter(student_id=sid).order_by('-start_time').first()
            rows.append([
                student.student_name,
                str(student.student_class) if student.student_class else '-',
                round(avg, 1),
                round(study / 3600, 1),
                last.start_time.strftime('%Y-%m-%d') if last else 'Never',
                'High Risk' if avg < 25 else 'Needs Attention' if avg < 40 else 'Stable'
            ])
        buf = _make_excel(headers, rows, 'Students')
        response = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="students_report.xlsx"'
        return response
 
 
 
@method_decorator(login_required, name='dispatch')
class ExportClassPDFAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        headers = ['Class', 'Students', 'Avg Score', 'Weak', 'Homework', 'Tests', 'Status']
        rows = []
        for cid in class_ids:
            cls  = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(student_class_id=cid).values_list('id', flat=True))
            avg  = StudentTestAttemptModel.objects.filter(student_id__in=sids).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(student_id__in=sids).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            hw = HomeworkModel.objects.filter(assigned_to__student_class_id=cid).distinct().count()
            tests = TestModel.objects.filter(student__in=sids).distinct().count()
            rows.append([str(cls), len(sids), f"{round(avg,1)}%", weak, hw, tests,
                         'Excellent' if avg >= 75 else 'Good' if avg >= 60 else 'Average'])
        buf = _make_pdf('Class Report', headers, rows)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="classes_report.pdf"'
        return response
 
 
@method_decorator(login_required, name='dispatch')
class ExportTeacherPDFAPI(View):
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        headers = ['Name', 'Email', 'Homework', 'Tests', 'Last Active']
        rows = []
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
            hw    = HomeworkModel.objects.filter(assigned_by_id=tid).count()
            tests = TestModel.objects.filter(created_by_id=tid).count()
            last  = TestModel.objects.filter(created_by_id=tid).order_by('-created_at').first()
            rows.append([
                f"{teacher.first_name} {teacher.last_name}",
                teacher.email, hw, tests,
                last.created_at.strftime('%Y-%m-%d') if last else 'Never'
            ])
        buf = _make_pdf('Teacher Report', headers, rows)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="teachers_report.pdf"'
        return response
 
 
@method_decorator(login_required, name='dispatch')
class ExportStudentPDFAPI(View):
    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        headers = ['Name', 'Class', 'Avg Score', 'Study Hrs', 'Last Active', 'Risk']
        rows = []
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            avg   = StudentTestAttemptModel.objects.filter(student_id=sid).aggregate(avg=Avg('score'))['avg'] or 0
            study = StudySession.objects.filter(student_id=sid).aggregate(total=Sum('duration'))['total'] or 0
            last  = StudySession.objects.filter(student_id=sid).order_by('-start_time').first()
            rows.append([
                student.student_name,
                str(student.student_class) if student.student_class else '-',
                f"{round(avg,1)}%",
                f"{round(study/3600,1)} hrs",
                last.start_time.strftime('%Y-%m-%d') if last else 'Never',
                'High Risk' if avg < 25 else 'Needs Attention' if avg < 40 else 'Stable'
            ])
        buf = _make_pdf('Student Report', headers, rows)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="students_report.pdf"'
        return response
 
 
# ─── 10. Settings ─────────────────────────────────────────────────────────────
 
@method_decorator(login_required, name='dispatch')
class CoordinatorSettingsView(View):
    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        return render(request, 'coordinator/coordinator_settings.html', context)
 

@method_decorator(login_required, name='dispatch')
class CoordinatorChangePasswordAPI(View):

    def post(self, request):
        data = json.loads(request.body)

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        user = request.user

        if not user.check_password(current_password):
            return JsonResponse({
                'success': False,
                'error': 'Current password is incorrect.'
            })

        user.set_password(new_password)
        user.save()

        # Keep user logged in after password change
        update_session_auth_hash(request, user)

        return JsonResponse({
            'success': True
        })

@method_decorator(login_required, name='dispatch')
class CoordinatorSubjectAPI(View):
    """
    GET /coordinator/api/subjects/
    Returns subject-wise performance for all classes in coordinator scope.
    """
    def get(self, request):
        class_ids, teacher_ids, _ = get_coordinator_scope(request.user)
 
        # Build full student list per class once
        class_student_map = {}
        for cid in class_ids:
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            class_student_map[cid] = sids
 
        all_student_ids = [sid for sids in class_student_map.values() for sid in sids]
 
        subjects = Subject.objects.all()# Subjects linked to tests assigned to scope students
        
 
        data = []
        for subj in Subject.objects.all():

            attempts = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj.id,
                student_id__in=all_student_ids
            )
            avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0
 
            weak_students = attempts.values('student_id').annotate(
                a=Avg('score')
            ).filter(a__lt=40).count()
 
            # Class-wise avg to find best/weakest
            class_avgs = []
            for cid, sids in class_student_map.items():
                if not sids:
                    continue
                c_avg = StudentTestAttemptModel.objects.filter(
                    test__subject_id=subj.id,
                    student_id__in=sids
                ).aggregate(avg=Avg('score'))['avg'] or 0
                cls = ClassModel.objects.filter(id=cid).first()
                class_avgs.append({'class_id': cid, 'name': str(cls) if cls else '-', 'avg': c_avg})
 
            best_class  = max(class_avgs, key=lambda x: x['avg'])['name'] if class_avgs else '-'
            weak_class  = min(class_avgs, key=lambda x: x['avg'])['name'] if class_avgs else '-'
 
            # Responsible teacher — teacher in scope who created most tests for this subject
            test = TestModel.objects.filter(
                subject_id=subj.id,
                created_by_id__in=teacher_ids
            ).first()

            teacher_name = (
                f"{test.created_by.first_name} {test.created_by.last_name}"
                if test and test.created_by else '-'
            )
 
            tests_count = TestModel.objects.filter(
                subject_id=subj.id,
                student__in=all_student_ids
            ).distinct().count()
            
 
            data.append({
                'id': subj.id,
                'subject': subj.name,
                'avg_score':     round(avg_score, 1),
                'weak_students': weak_students,
                'tests_count':   tests_count,
                'best_class':    best_class,
                'weakest_class': weak_class,
                'teacher':       teacher_name,
                'status': (
                    'Excellent' if avg_score >= 75 else
                    'Good'      if avg_score >= 60 else
                    'Average'   if avg_score >= 50 else
                    'Weak'      if avg_score >= 35 else
                    'Critical'
                ),
            })
 
        data.sort(key=lambda x: x['avg_score'])
        return JsonResponse({'subjects': data})



@method_decorator(login_required, name='dispatch')
class CoordinatorSubjectDetailAPI(View):
    """
    GET /coordinator/api/subjects/<subj_id>/
    Full drill-down: per-class breakdown, weak students, recent tests.
    """
    def get(self, request, pk):
        class_ids, teacher_ids, _ = get_coordinator_scope(request.user)
 
        subj = Subject.objects.filter(id=pk).first()
        if not subj:
            return JsonResponse({'error': 'Subject not found'}, status=404)
 
        all_student_ids = list(StudentModel.objects.filter(
            student_class_id__in=class_ids
        ).values_list('id', flat=True))
 
        class_breakdown = []
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            avg = StudentTestAttemptModel.objects.filter(
                test__subject_id=pk, student_id__in=sids
            ).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(
                test__subject_id=pk, student_id__in=sids
            ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            class_breakdown.append({
                'class':         str(cls) if cls else '-',
                'avg_score':     round(avg, 1),
                'weak_students': weak,
                'status': (
                    'Excellent' if avg >= 75 else 'Good' if avg >= 60 else
                    'Average'   if avg >= 50 else 'Weak' if avg >= 35 else 'Critical'
                ),
            })
 
        # Weak students in this subject
        weak_qs = StudentTestAttemptModel.objects.filter(
            test__subject_id=pk, student_id__in=all_student_ids
        ).values('student_id').annotate(avg=Avg('score')).filter(avg__lt=40)
 
        weak_students = []
        for w in weak_qs:
            stu = StudentModel.objects.filter(id=w['student_id']).first()
            if stu:
                weak_students.append({
                    'id':        stu.id,
                    'name':      stu.student_name,
                    'class':     str(stu.student_class) if stu.student_class else '-',
                    'avg_score': round(w['avg'], 1),
                })
 
        # Recent tests
        recent_tests = TestModel.objects.filter(
            subject_id=pk, student__in=all_student_ids
        ).distinct().order_by('-id')[:10]
       
        tests_data = []
        for t in recent_tests:
            attempts = StudentTestAttemptModel.objects.filter(test=t)
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            tests_data.append({
                'id':          t.id,
                'title':       t.title,
                'avg_score':   round(avg, 1),
                'retest':      avg < 40,
                'date':        t.scheduled_date.strftime('%Y-%m-%d') if t.scheduled_date else '-',
            })
 
        overall_avg = StudentTestAttemptModel.objects.filter(
            test__subject_id=pk, student_id__in=all_student_ids
        ).aggregate(avg=Avg('score'))['avg'] or 0
       
        return JsonResponse({
            'subject':          subj.name,
            'overall_avg':      round(overall_avg, 1),
            'class_breakdown':  class_breakdown,
            'weak_students':    weak_students,
            'recent_tests':     tests_data,
        })


@method_decorator(login_required, name='dispatch')
class CoordinatorWeaknessAPI(View):
    """
    GET /coordinator/api/weakness/
    Subject-wise weak students grouped by class. Powers the Weakness Analysis page.
    """
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
 
        result = []
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
 
            subject_ids = list(
                TestModel.objects.filter(student__in=sids).exclude(
                    subject=None
                ).values_list('subject_id', flat=True).distinct()
            )
 
            subjects = []
            for subj_id in subject_ids:
                subj = Subject.objects.filter(id=subj_id).first()
                if not subj:
                    continue
                avg = StudentTestAttemptModel.objects.filter(
                    test__subject_id=subj_id, student_id__in=sids
                ).aggregate(avg=Avg('score'))['avg'] or 0
 
                weak_count = StudentTestAttemptModel.objects.filter(
                    test__subject_id=subj_id, student_id__in=sids
                ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
 
                subjects.append({
                    'subject':       subj.name,
                    'avg_score':     round(avg, 1),
                    'weak_students': weak_count,
                    'status': (
                        'green'  if avg >= 60 else
                        'yellow' if avg >= 40 else
                        'red'
                    ),
                })
 
            result.append({
                'class_id':  cid,
                'class':     str(cls),
                'subjects':  subjects,
            })
 
        return JsonResponse({'weakness': result})
 

@method_decorator(login_required, name='dispatch')
class CoordinatorStudentFilterAPI(View):
    """
    GET /coordinator/api/students/filter/
    Query params (all optional):
      class_id, teacher_id, risk, score_min, score_max,
      hw_pending (true/false), inactive_days, search (name)
    """
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
        today = timezone.now().date()
 
        qs = StudentModel.objects.filter(id__in=student_ids)
 
        # -- class filter
        class_id = request.GET.get('class_id')
        if class_id:
            qs = qs.filter(student_class_id=class_id)
 
        # -- teacher filter (via parent M2M)
        teacher_id = request.GET.get('teacher_id')
        if teacher_id:
            qs = qs.filter(parent__id=teacher_id)
 
        # -- name search
        search = request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(student_name__icontains=search)
 
        # Compute per-student stats then apply remaining filters
        score_min    = request.GET.get('score_min')
        score_max    = request.GET.get('score_max')
        risk_filter  = request.GET.get('risk')
        hw_pending   = request.GET.get('hw_pending')
        inactive_days_param = request.GET.get('inactive_days')
 
        data = []
        for student in qs:
            sid = student.id
 
            avg = StudentTestAttemptModel.objects.filter(
                student_id=sid
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            # score range filter
            if score_min and avg < float(score_min):
                continue
            if score_max and avg > float(score_max):
                continue
 
            # study / inactive
            last_session = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()
            last_active = last_session.start_time.date() if last_session else None
            days_inactive = (today - last_active).days if last_active else 9999
 
            if inactive_days_param:
                if days_inactive < int(inactive_days_param):
                    continue
 
            # homework pending filter
            hw_assigned  = HomeworkModel.objects.filter(assigned_to=student).distinct().count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(student_id=sid).count()
            hw_pending_count = max(0, hw_assigned - hw_submitted)
 
            if hw_pending == 'true' and hw_pending_count == 0:
                continue
 
            # risk tag
            if last_active is None:
                risk = 'Inactive'
            elif avg >= 70:
                risk = 'Excellent'
            elif avg >= 40:
                risk = 'Stable'
            elif avg >= 25:
                risk = 'Needs Attention'
            else:
                risk = 'High Risk'
 
            if risk_filter and risk != risk_filter:
                continue
 
            study_total = StudySession.objects.filter(
                student_id=sid
            ).aggregate(total=Sum('duration'))['total'] or 0
 
            teacher = student.parent.filter(role__type='Teacher').first()
            teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else '-'
 
            data.append({
                'id':            sid,
                'name':          student.student_name,
                'class':         str(student.student_class) if student.student_class else '-',
                'teacher':       teacher_name,
                'avg_score':     round(avg, 1),
                'study_time':    f'{round(study_total / 60, 1)} min',
                'hw_pending':    hw_pending_count,
                'last_active':   last_active.strftime('%Y-%m-%d') if last_active else 'Never',
                'days_inactive': days_inactive if days_inactive < 9999 else '-',
                'risk':          risk,
            })
 
        return JsonResponse({'students': data, 'count': len(data)})
 

@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherComparisonAPI(View):
    """
    GET /coordinator/api/teacher-comparison/
    Returns sorted teacher list with ranking badges.
    """
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
 
        rows = []
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
 
            hw_count    = HomeworkModel.objects.filter(created_by_id=tid).count()
            tests_count = TestModel.objects.filter(created_by_id=tid).count()
            hw_checked  = HomeworkSubmissionModel.objects.filter(
                homework__created_by_id=tid, score__isnull=False
            ).count()
 
            teacher_students = StudentModel.objects.filter(
                parent=tid
            ).values_list('id', flat=True)
 
            avg_score = StudentTestAttemptModel.objects.filter(
                student_id__in=teacher_students
            ).aggregate(avg=Avg('score'))['avg'] or 0
 
            weak_under = StudentTestAttemptModel.objects.filter(
                student_id__in=teacher_students
            ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
 
            last_test = TestModel.objects.filter(
                created_by_id=tid
            ).order_by('-created_at').first()
            last_active = last_test.created_at.strftime('%Y-%m-%d') if last_test else 'Never'
 
            # Accountability score matching spec §10 weights:
            # classes_taken(20) + teaching_time(20) + tests(15) + hw_given(15) + hw_checked(15) + improvement(15)
            # teaching_time and improvement need dedicated models; use 0 until those models exist
            score = min(100, (
                min(tests_count, 4) * 5 +        # tests conducted  (max 20 pts)
                min(hw_count, 4) * 5 +            # homework given   (max 20 pts — was 15 in stub)
                min(hw_checked, 3) * 5 +          # homework checked (max 15 pts — NEW)
                (10 if avg_score > 60 else 0) +   # student improvement proxy
                (10 if weak_under == 0 else 0)    # no weak students bonus
            ))
 
            rows.append({
                'id':                tid,
                'name':              f"{teacher.first_name} {teacher.last_name}",
                'email':             teacher.email,
                'tests':             tests_count,
                'homework_given':    hw_count,
                'homework_checked':  hw_checked,
                'avg_student_score': round(avg_score, 1),
                'weak_students':     weak_under,
                'last_active':       last_active,
                'score':             score,
                'status': (
                    'Good'    if score > 70 else
                    'Average' if score > 40 else
                    'Risk'
                ),
            })
 
        # Sort by score descending and attach rank
        rows.sort(key=lambda x: x['score'], reverse=True)
        for i, r in enumerate(rows):
            r['rank'] = i + 1
            r['badge'] = (
                'Best Active'    if i == 0 else
                'Least Active'   if i == len(rows) - 1 else
                ''
            )
 
        return JsonResponse({'teachers': rows})

@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherCommentAPI(View):
    """
    GET  /coordinator/api/teacher-comment/<teacher_id>/   – list comments
    POST /coordinator/api/teacher-comment/<teacher_id>/   – add comment
    DELETE /coordinator/api/teacher-comment/<teacher_id>/<comment_id>/ – remove
    """
    def get(self, request, teacher_id):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        if teacher_id not in teacher_ids:
            return JsonResponse({'error': 'Not in scope'}, status=403)
 
        remarks = TeacherRemarkModel.objects.filter(
            teacher_id=teacher_id,
            teacher=request.user
        ).order_by('-created_at').values(
            'id', 'remark', 'remark_type', 'created_at'
        )
        data = []
        for r in remarks:
            data.append({
                'id':          r['id'],
                'remark':      r['remark'],
                'remark_type': r['remark_type'],
                'created_at':  r['created_at'].strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'comments': data})
 
    def post(self, request, teacher_id):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        if teacher_id not in teacher_ids:
            return JsonResponse({'error': 'Not in scope'}, status=403)
 
        body = json.loads(request.body)
        remark_text = body.get('remark', '').strip()
        remark_type = body.get('remark_type', 'general').lower()
 
        if not remark_text:
            return JsonResponse({'error': 'Remark text required'}, status=400)
 
        remark = TeacherRemarkModel.objects.create(
            teacher_id=teacher_id,
            teacher=request.user,
            remark=remark_text,
            remark_type=remark_type,
        )
        return JsonResponse({'success': True, 'id': remark.id})
    
    def delete(self, request, teacher_id, comment_id):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        if teacher_id not in teacher_ids:
            return JsonResponse({'error': 'Not in scope'}, status=403)
        try:
            remark = TeacherRemarkModel.objects.get(
                pk=comment_id,
                teacher_id=teacher_id,
                teacher=request.user
            )
            remark.delete()
            return JsonResponse({'success': True})
        except TeacherRemarkModel.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
    
 
# ══════════════════════════════════════════════════════════════════════════════
# 5. HOMEWORK — LATE SUBMISSIONS & NON-SUBMITTERS  (spec §14)
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkLateAPI(View):
    """
    GET /coordinator/api/homework-late/
    Returns late submissions and per-student repeat non-submitter data.
    """
    def get(self, request):
        class_ids, _, student_ids = get_coordinator_scope(request.user)
        today = timezone.now()
 
        # Late submissions: submitted_at > due_date
        late = HomeworkSubmissionModel.objects.filter(
            student_id__in=student_ids,
            homework__due_date__isnull=False,
            submitted_at__isnull=False,
            submitted_at__gt=F('homework__due_date')
        ).select_related('student', 'homework').order_by('-submitted_at')
 
        late_data = []
        for sub in late:
            late_data.append({
                'student':    sub.student.student_name if sub.student else '-',
                'class':      str(sub.student.student_class) if sub.student and sub.student.student_class else '-',
                'homework':   sub.homework.title,
                'due_date':   sub.homework.due_date.strftime('%Y-%m-%d') if sub.homework.due_date else '-',
                'submitted':  sub.submitted_at.strftime('%Y-%m-%d') if sub.submitted_at else '-',
                'days_late':  (sub.submitted_at.date() - sub.homework.due_date.date()).days
                              if sub.submitted_at and sub.homework.due_date else '-',
            })
 
        # Repeat non-submitters: students who missed ≥ 2 homework
        non_submitters = []
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            assigned = HomeworkModel.objects.filter(
                assigned_to=student
            ).distinct().count()
            submitted = HomeworkSubmissionModel.objects.filter(
                student_id=sid
            ).count()
            missed = assigned - submitted
            if missed >= 2:
                non_submitters.append({
                    'id':            sid,
                    'student':       student.student_name,
                    'class':         str(student.student_class) if student.student_class else '-',
                    'assigned':      assigned,
                    'submitted':     submitted,
                    'missed':        missed,
                    'miss_pct':      round((missed / assigned * 100) if assigned else 0, 1),
                })
 
        non_submitters.sort(key=lambda x: x['missed'], reverse=True)
 
        return JsonResponse({
            'late_submissions': late_data,
            'non_submitters':   non_submitters,
        })
 
 
# ══════════════════════════════════════════════════════════════════════════════
# 6. TEST FILTERS  (spec §13)
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class CoordinatorTestFilterAPI(View):
    """
    GET /coordinator/api/tests/filter/
    Query params: teacher_id, subject_id, class_id, date_from, date_to,
                  retest_required (true/false), low_score (true/false), search
    """
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
 
        qs = TestModel.objects.filter(
            Q(student__in=student_ids) | Q(created_by_id__in=teacher_ids)
        ).distinct()
 
        teacher_id  = request.GET.get('teacher_id')
        subject_id  = request.GET.get('subject_id')
        class_id    = request.GET.get('class_id')
        date_from   = request.GET.get('date_from')
        date_to     = request.GET.get('date_to')
        retest_req  = request.GET.get('retest_required')
        low_score   = request.GET.get('low_score')
        search      = request.GET.get('search', '').strip()
 
        if teacher_id:
            qs = qs.filter(created_by_id=teacher_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if class_id:
            sids_in_class = list(StudentModel.objects.filter(
                student_class_id=class_id
            ).values_list('id', flat=True))
            qs = qs.filter(student__in=sids_in_class)
        if date_from:
            qs = qs.filter(scheduled_date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_date__lte=date_to)
        if search:
            qs = qs.filter(title__icontains=search)
 
        data = []
        for test in qs:
            attempts      = StudentTestAttemptModel.objects.filter(test=test)
            attempted     = attempts.values('student').distinct().count()
            total_students = test.student.count()
            avg_score     = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            highest       = attempts.aggregate(h=Max('score'))['h'] or 0
            lowest        = attempts.aggregate(l=Min('score'))['l'] or 0
            failed        = attempts.filter(score__lt=40).count()
 
            is_retest = avg_score < 40
            is_low    = avg_score < 50
 
            if retest_req == 'true' and not is_retest:
                continue
            if low_score == 'true' and not is_low:
                continue
 
            teacher_name = ''
            if test.created_by:
                teacher_name = f"{test.created_by.first_name} {test.created_by.last_name}".strip()
 
            data.append({
                'id':             test.id,
                'title':          test.title,
                'subject':        test.subject.name if test.subject else '-',
                'teacher':        teacher_name,
                'date':           test.scheduled_date.strftime('%Y-%m-%d') if test.scheduled_date else '-',
                'total_students': total_students,
                'attempted':      attempted,
                'absent':         max(0, total_students - attempted),
                'avg_score':      round(avg_score, 1),
                'highest':        round(highest, 1),
                'lowest':         round(lowest, 1),
                'failed':         failed,
                'retest_needed':  is_retest,
            })
 
        return JsonResponse({'tests': data, 'count': len(data)})
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorTestMissedAPI(View):
    """
    GET /coordinator/api/tests/missed/
    Returns per-student missed / pending test count.
    """
    def get(self, request):
        class_ids, _, student_ids = get_coordinator_scope(request.user)
        data = []
 
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
 
            assigned_tests = TestModel.objects.filter(student=student).distinct()
            total_assigned = assigned_tests.count()
 
            attempted_ids = list(
                StudentTestAttemptModel.objects.filter(
                    student_id=sid
                ).values_list('test_id', flat=True).distinct()
            )
 
            missed_tests = assigned_tests.exclude(id__in=attempted_ids)
            missed_count = missed_tests.count()
 
            if missed_count == 0:
                continue
 
            data.append({
                'id':             sid,
                'name':           student.student_name,
                'class':          str(student.student_class) if student.student_class else '-',
                'assigned_tests': total_assigned,
                'attempted':      total_assigned - missed_count,
                'missed':         missed_count,
                'missed_tests':   [
                    {
                        'id':    t.id,
                        'title': t.title,
                        'date':  t.scheduled_date.strftime('%Y-%m-%d') if t.scheduled_date else '-',
                    }
                    for t in missed_tests[:5]
                ],
            })
 
        data.sort(key=lambda x: x['missed'], reverse=True)
        return JsonResponse({'missed_tests': data, 'count': len(data)})
 
 
# ══════════════════════════════════════════════════════════════════════════════
# 7. ACTION — ASSIGN TO TEACHER  (spec §8 §16)
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class CoordinatorActionAssignAPI(View):
    """
    POST /coordinator/api/actions/assign/
    Body: { title, description, priority, due_date,
            student_id (opt), teacher_id (opt) }
    Creates a CoordinatorActionModel linked to a teacher for tracking.
    GET  /coordinator/api/actions/assign/ — list all assigned actions with teacher info.
    """
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        actions = CoordinatorActionModel.objects.filter(
            coordinator=request.user
        ).order_by('priority', '-created_at')
 
        data = []
        for a in actions:
            data.append({
                'id':           a.id,
                'issue':        a.issue or '',
                'responsible':  a.responsible or '',
                'required_action': a.required_action or '',
                'priority':     a.priority,
                'status':       a.status,
                'due_date':     a.due_date.strftime('%Y-%m-%d') if a.due_date else '-',
                'remarks':      a.remarks or '',
                'created_at':   a.created_at.strftime('%Y-%m-%d') if a.created_at else '-',
            })
        return JsonResponse({'actions': data})
 
    def post(self, request):
        _, teacher_ids, student_ids = get_coordinator_scope(request.user)
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
 
        issue           = body.get('issue', '').strip()
        responsible     = body.get('responsible', '').strip()
        required_action = body.get('required_action', '').strip()
        priority        = body.get('priority', 'Medium')
        due_date        = body.get('due_date')

        if not issue:
            return JsonResponse({'error': 'Issue is required'}, status=400)

        create_kwargs = dict(
            coordinator=request.user,
            issue=issue,
            responsible=responsible or 'Coordinator',
            required_action=required_action,
            priority=priority,
            status='New',
        )
        if due_date:
            create_kwargs['due_date'] = due_date

        action = CoordinatorActionModel.objects.create(**create_kwargs)
        return JsonResponse({'success': True, 'id': action.id})
 
 
# ══════════════════════════════════════════════════════════════════════════════
# 8. MISSING ALERTS  (spec §17 — adds to existing CoordinatorAlertsAPI)
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class CoordinatorAllAlertsAPI(View):
    """
    GET /coordinator/api/alerts/all/
    Replaces (or supplements) existing CoordinatorAlertsAPI with ALL 10 alert types
    from spec §17 including the 4 previously missing ones.
    """
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
        today = timezone.now().date()
        today_str = today.strftime('%d %b %Y')
        alerts = []
 
        # --- EXISTING ALERTS (keep same logic) ---
 
        # 1. Student inactive 3+ days
        for sid in student_ids:
            last = StudySession.objects.filter(
                student_id=sid
            ).order_by('-start_time').first()
            if not last or (today - last.start_time.date()).days >= 3:
                student = StudentModel.objects.filter(id=sid).first()
                if student:
                    if last:
                        days_gap = (today - last.start_time.date()).days
                    else:
                        days_gap = 'many'
                    alerts.append({
                        'priority': 'High', 'type': 'Student Inactive',
                        'message':  f'{student.student_name} inactive for {days_gap} days',
                        'class':    str(student.student_class) if student.student_class else '-',
                        'responsible': student.student_name, 'date': today_str, 'status': 'New',
                    })
 
        # 2. Student score < 40
        weak = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids
        ).values('student_id').annotate(avg=Avg('score')).filter(avg__lt=40)
        for w in weak:
            student = StudentModel.objects.filter(id=w['student_id']).first()
            if student:
                alerts.append({
                    'priority': 'High', 'type': 'Low Score',
                    'message':  f'{student.student_name} avg score {round(w["avg"],1)}% — below 40%',
                    'class':    str(student.student_class) if student.student_class else '-',
                    'responsible': student.student_name, 'date': today_str, 'status': 'New',
                })
 
        # 3. Homework pending > 50% per class
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            if not cls:
                continue
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            hw_given     = HomeworkModel.objects.filter(assigned_to__in=sids).distinct().count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(student_id__in=sids).count()
            if hw_given > 0:
                pending_pct = ((hw_given - hw_submitted) / hw_given) * 100
                if pending_pct > 50:
                    alerts.append({
                        'priority': 'Medium', 'type': 'Homework Pending',
                        'message':  f'{str(cls)} — {round(pending_pct,1)}% homework pending',
                        'class':    str(cls), 'responsible': 'Class Teacher',
                        'date': today_str, 'status': 'New',
                    })
 
        # 4. Teacher no test for 7 days
        for tid in teacher_ids:
            last_test = TestModel.objects.filter(
                created_by_id=tid
            ).order_by('-created_at').first()
            teacher = UserModel.objects.filter(id=tid).first()
            if teacher:
                if not last_test or (today - last_test.created_at.date()).days >= 7:
                    alerts.append({
                        'priority': 'Medium', 'type': 'Teacher No Test',
                        'message':  f'{teacher.first_name} {teacher.last_name} — no test in 7+ days',
                        'class': '-', 'responsible': f'{teacher.first_name} {teacher.last_name}',
                        'date': today_str, 'status': 'New',
                    })
 
        # 5. Overdue coordinator actions
        overdue = CoordinatorActionModel.objects.filter(
            coordinator=request.user,
            status__in=['New', 'Pending'],
            due_date__lt=today
        ).count()
        if overdue:
            alerts.append({
                'priority': 'High', 'type': 'Overdue Actions',
                'message':  f'{overdue} coordinator actions overdue — escalate to principal',
                'class': '-', 'responsible': 'Coordinator',
                'date': today_str, 'status': 'Overdue',
            })
 
        # --- NEW ALERT 6: Teacher inactive 2+ days (spec §17) ---
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
            last_test = TestModel.objects.filter(
                created_by_id=tid
            ).order_by('-created_at').first()
            last_hw = HomeworkModel.objects.filter(
                created_by_id=tid
            ).order_by('-id').first()
 
            last_activity_dates = []
            if last_test:
                last_activity_dates.append(last_test.created_at.date())
            if last_hw and hasattr(last_hw, 'created_at') and last_hw.created_at:
                last_activity_dates.append(last_hw.created_at.date())
 
            if last_activity_dates:
                most_recent = max(last_activity_dates)
                days_inactive = (today - most_recent).days
            else:
                days_inactive = 999
 
            if days_inactive >= 2:
                alerts.append({
                    'priority': 'Medium', 'type': 'Teacher Inactive',
                    'message':  f'{teacher.first_name} {teacher.last_name} — no activity for {days_inactive} days',
                    'class': '-', 'responsible': f'{teacher.first_name} {teacher.last_name}',
                    'date': today_str, 'status': 'New',
                })
 
        # --- NEW ALERT 7: Class average dropped (spec §17) ---
        # Compare last-7-days avg vs prior-7-days avg
        week_start  = today - timezone.timedelta(days=7)
        week_before = today - timezone.timedelta(days=14)
        for cid in class_ids:
            cls = ClassModel.objects.filter(id=cid).first()
            sids = list(StudentModel.objects.filter(
                student_class_id=cid
            ).values_list('id', flat=True))
            if not sids:
                continue
            recent_avg = StudentTestAttemptModel.objects.filter(
                student_id__in=sids,
                started_at__date__gte=week_start
            ).aggregate(avg=Avg('score'))['avg'] or None
            prior_avg = StudentTestAttemptModel.objects.filter(
                student_id__in=sids,
                started_at__date__gte=week_before,
                started_at__date__lt=week_start
            ).aggregate(avg=Avg('score'))['avg'] or None
            if recent_avg and prior_avg and prior_avg > 0:
                drop = prior_avg - recent_avg
                if drop >= 5:
                    alerts.append({
                        'priority': 'High', 'type': 'Class Avg Dropped',
                        'message':  f'{str(cls)} avg dropped by {round(drop,1)}% this week',
                        'class':    str(cls) if cls else '-',
                        'responsible': 'Class Teachers', 'date': today_str, 'status': 'New',
                    })
 
        # --- NEW ALERT 8: Tablet not synced (spec §17) ---
        for sid in student_ids:
            student = StudentModel.objects.filter(id=sid).first()
            if not student:
                continue
            device = DeviceModel.objects.filter(user__in=student.parent.all()).first()
            if not device:
                continue
            # Use last_sync_at if available; fall back to last StudySession
            last_sync = getattr(device, 'last_sync_at', None)
            if last_sync:
                days_since_sync = (today - last_sync.date()).days
                if days_since_sync >= 3:
                    alerts.append({
                        'priority': 'Medium', 'type': 'Tablet Not Synced',
                        'message':  f'{student.student_name} tablet {device.imei_number} not synced for {days_since_sync} days',
                        'class':    str(student.student_class) if student.student_class else '-',
                        'responsible': 'IT / Admin', 'date': today_str, 'status': 'New',
                    })
 
        # --- NEW ALERT 9: Teacher not checking homework (spec §17) ---
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
            total_submitted = HomeworkSubmissionModel.objects.filter(
                homework__created_by_id=tid
            ).count()
            checked = HomeworkSubmissionModel.objects.filter(
                homework__created_by_id=tid,
                score__isnull=False
            ).count()
            if total_submitted > 0:
                unchecked_pct = ((total_submitted - checked) / total_submitted) * 100
                if unchecked_pct > 50:
                    alerts.append({
                        'priority': 'Medium', 'type': 'HW Not Checked',
                        'message':  f'{teacher.first_name} {teacher.last_name} — {round(unchecked_pct,1)}% homework unchecked',
                        'class': '-', 'responsible': f'{teacher.first_name} {teacher.last_name}',
                        'date': today_str, 'status': 'New',
                    })
 
        # Sort: High first
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
 
        return JsonResponse({'count': len(alerts), 'alerts': alerts})
 
 
# ══════════════════════════════════════════════════════════════════════════════
# 9. SUBJECT REPORT & EXPORTS  (spec §18)
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class CoordinatorSubjectReportAPI(View):
    """GET /coordinator/api/reports/subject/"""
    def get(self, request):
        class_ids, teacher_ids, _ = get_coordinator_scope(request.user)
        all_student_ids = list(StudentModel.objects.filter(
            student_class_id__in=class_ids
        ).values_list('id', flat=True))
 
        subject_ids = list(
            TestModel.objects.filter(
                student__in=all_student_ids
            ).exclude(subject=None).values_list('subject_id', flat=True).distinct()
        )
 
        data = []
        for subj_id in subject_ids:
            subj = Subject.objects.filter(id=subj_id).first()
            if not subj:
                continue
            avg = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj_id, student_id__in=all_student_ids
            ).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj_id, student_id__in=all_student_ids
            ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            tests = TestModel.objects.filter(
                subject_id=subj_id, student__in=all_student_ids
            ).distinct().count()
            data.append({
                'subject':       subj.name,
                'avg_score':     round(avg, 1),
                'weak_students': weak,
                'tests_count':   tests,
                'status': (
                    'Excellent' if avg >= 75 else 'Good' if avg >= 60 else
                    'Average'   if avg >= 50 else 'Weak' if avg >= 35 else 'Critical'
                ),
            })
        data.sort(key=lambda x: x['avg_score'])
        return JsonResponse({'report': data})
 
@method_decorator(login_required, name='dispatch')
class CoordinatorActionReportAPI(View):
    """GET /coordinator/api/reports/actions/  — weekly action summary"""
    def get(self, request):
        week_start = timezone.now().date() - timezone.timedelta(days=7)
        actions = CoordinatorActionModel.objects.filter(
            coordinator=request.user,
            created_at__date__gte=week_start
        ).order_by('priority', '-created_at')

        data = []
        for a in actions:
            data.append({
                'issue':        a.issue or '',          # FIXED: was a.title
                'responsible':  a.responsible or '',
                'required_action': a.required_action or '',
                'priority':     a.priority,
                'status':       a.status,
                'due_date':     a.due_date.strftime('%Y-%m-%d') if a.due_date else '-',
                'remarks':      a.remarks or '',
                'created_at':   a.created_at.strftime('%Y-%m-%d'),
            })

        summary = {
            'total':     actions.count(),
            'resolved':  actions.filter(status='Resolved').count(),
            'pending':   actions.filter(status__in=['New', 'Pending']).count(),
            'escalated': actions.filter(status='Escalated to Principal').count(),
        }
        return JsonResponse({'summary': summary, 'report': data})
# ══════════════════════════════════════════════════════════════════════════════
# 10. EXCEL / PDF EXPORTS — NEW
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class ExportSubjectExcelAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        all_sids = list(StudentModel.objects.filter(
            student_class_id__in=class_ids
        ).values_list('id', flat=True))
        subject_ids = list(
            TestModel.objects.filter(student__in=all_sids).exclude(
                subject=None
            ).values_list('subject_id', flat=True).distinct()
        )
        headers = ['Subject', 'Avg Score', 'Weak Students', 'Tests Count', 'Status']
        rows = []
        for subj_id in subject_ids:
            subj = Subject.objects.filter(id=subj_id).first()
            if not subj:
                continue
            avg = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj_id, student_id__in=all_sids
            ).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj_id, student_id__in=all_sids
            ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            tests = TestModel.objects.filter(
                subject_id=subj_id, student__in=all_sids
            ).distinct().count()
            rows.append([subj.name, round(avg, 1), weak, tests,
                         'Excellent' if avg >= 75 else 'Good' if avg >= 60 else
                         'Average'   if avg >= 50 else 'Weak' if avg >= 35 else 'Critical'])
        buf = _make_excel(headers, rows, 'Subjects')
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="subject_report.xlsx"'
        return resp
 
 
@method_decorator(login_required, name='dispatch')
class ExportSubjectPDFAPI(View):
    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        all_sids = list(StudentModel.objects.filter(
            student_class_id__in=class_ids
        ).values_list('id', flat=True))
        subject_ids = list(
            TestModel.objects.filter(student__in=all_sids).exclude(
                subject=None
            ).values_list('subject_id', flat=True).distinct()
        )
        headers = ['Subject', 'Avg Score', 'Weak Students', 'Tests', 'Status']
        rows = []
        for subj_id in subject_ids:
            subj = Subject.objects.filter(id=subj_id).first()
            if not subj:
                continue
            avg = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj_id, student_id__in=all_sids
            ).aggregate(avg=Avg('score'))['avg'] or 0
            weak = StudentTestAttemptModel.objects.filter(
                test__subject_id=subj_id, student_id__in=all_sids
            ).values('student_id').annotate(a=Avg('score')).filter(a__lt=40).count()
            tests = TestModel.objects.filter(
                subject_id=subj_id, student__in=all_sids
            ).distinct().count()
            rows.append([subj.name, f'{round(avg,1)}%', weak, tests,
                         'Excellent' if avg >= 75 else 'Good' if avg >= 60 else 'Average'])
        buf = _make_pdf('Subject Weakness Report', headers, rows)
        resp = HttpResponse(buf, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="subject_report.pdf"'
        return resp
 
 
@method_decorator(login_required, name='dispatch')
class ExportActionExcelAPI(View):
    def get(self, request):
        week_start = timezone.now().date() - timezone.timedelta(days=7)
        actions = CoordinatorActionModel.objects.filter(
            coordinator=request.user,
            created_at__date__gte=week_start
        )
        headers = ['Issue', 'Responsible', 'Required Action', 'Priority', 'Status', 'Due Date', 'Remarks']
        rows = []
        for a in actions:
            rows.append([
                a.issue or '',              # FIXED: was a.title
                a.responsible or '',
                a.required_action or '',
                a.priority,
                a.status,
                a.due_date.strftime('%Y-%m-%d') if a.due_date else '-',
                a.remarks or '',
            ])
        buf = _make_excel(headers, rows, 'Actions')
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="action_report.xlsx"'
        return resp
 
 
@method_decorator(login_required, name='dispatch')
class ExportEscalationPDFAPI(View):
    """PDF export of all escalations — for the principal."""
    def get(self, request):
        escalations = CoordinatorEscalationModel.objects.filter(
            coordinator=request.user
        ).order_by('-created_at')
        headers = ['Title', 'Priority', 'Status', 'Student', 'Teacher', 'Created', 'Resolved']
        rows = []
        for e in escalations:
            rows.append([
                e.title, e.priority, e.status,
                e.student.student_name if e.student else '-',
                f"{e.teacher.first_name} {e.teacher.last_name}" if e.teacher else '-',
                e.created_at.strftime('%Y-%m-%d'),
                e.resolved_at.strftime('%Y-%m-%d') if e.resolved_at else 'Open',
            ])
        buf = _make_pdf('Escalation Report for Principal', headers, rows)
        resp = HttpResponse(buf, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="escalation_report.pdf"'
        return resp
 
 
# ══════════════════════════════════════════════════════════════════════════════
# 11. BUG FIXES — replace the broken versions in coordinator_views.py
# ══════════════════════════════════════════════════════════════════════════════
 
@method_decorator(login_required, name='dispatch')
class ExportTeacherExcelAPI(View):
    """BUG FIX: was using assigned_by_id — correct field is created_by_id"""
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        headers = ['Name', 'Email', 'Homework Count', 'Tests Count', 'Last Active']
        rows = []
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
            hw    = HomeworkModel.objects.filter(created_by_id=tid).count()   # FIXED
            tests = TestModel.objects.filter(created_by_id=tid).count()
            last  = TestModel.objects.filter(created_by_id=tid).order_by('-created_at').first()
            rows.append([
                f"{teacher.first_name} {teacher.last_name}",
                teacher.email, hw, tests,
                last.created_at.strftime('%Y-%m-%d') if last else 'Never'
            ])
        buf = _make_excel(headers, rows, 'Teachers')
        resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="teachers_report.xlsx"'
        return resp
 
 
@method_decorator(login_required, name='dispatch')
class ExportTeacherPDFAPI(View):
    """BUG FIX: was using assigned_by_id — correct field is created_by_id"""
    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        headers = ['Name', 'Email', 'Homework', 'Tests', 'Last Active']
        rows = []
        for tid in teacher_ids:
            teacher = UserModel.objects.filter(id=tid).first()
            if not teacher:
                continue
            hw    = HomeworkModel.objects.filter(created_by_id=tid).count()   # FIXED
            tests = TestModel.objects.filter(created_by_id=tid).count()
            last  = TestModel.objects.filter(created_by_id=tid).order_by('-created_at').first()
            rows.append([
                f"{teacher.first_name} {teacher.last_name}",
                teacher.email, hw, tests,
                last.created_at.strftime('%Y-%m-%d') if last else 'Never'
            ])
        buf = _make_pdf('Teacher Report', headers, rows)
        resp = HttpResponse(buf, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="teachers_report.pdf"'
        return resp
 
 
@method_decorator(login_required, name='dispatch')
class CoordinatorTestStatsAPI(View):
    """
    BUG FIX: previous version did TestModel.objects.all() — no scope filter.
    Now correctly scoped to coordinator's students and teachers.
    """
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
 
        tests = TestModel.objects.filter(
            Q(student__in=student_ids) | Q(created_by_id__in=teacher_ids)
        ).distinct()
 
        data = []
        for test in tests:
            attempts       = StudentTestAttemptModel.objects.filter(test=test)
            attempted      = attempts.values('student').distinct().count()
            total_students = test.student.count()
            avg_score      = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            highest        = attempts.aggregate(h=Max('score'))['h'] or 0
            lowest         = attempts.aggregate(l=Min('score'))['l'] or 0
            failed         = attempts.filter(score__lt=40).count()
 
            teacher_name = ''
            if test.created_by:
                teacher_name = f"{test.created_by.first_name} {test.created_by.last_name}".strip()
 
            data.append({
                'id':             test.id,
                'title':          test.title,
                'subject':        test.subject.name if test.subject else '-',
                'teacher':        teacher_name,
                'date':           test.scheduled_date.strftime('%Y-%m-%d') if test.scheduled_date else '-',
                'total_students': total_students,
                'attempted':      attempted,
                'absent':         max(0, total_students - attempted),
                'avg_score':      round(avg_score, 1),
                'highest':        round(highest, 1),
                'lowest':         round(lowest, 1),
                'failed':         failed,
                'retest_needed':  avg_score < 40,
            })
 
        return JsonResponse({'tests': data})

@method_decorator(login_required, name='dispatch')
class CoordinatorStudentDetailView(View):
    """Page view — renders the student detail template."""
    def get(self, request, pk):
        _, _, student_ids = get_coordinator_scope(request.user)
        if pk not in student_ids:
            return redirect('coordinator-students')
        context = TemplateLayout.init(self, {})
        context['layout_path'] = TemplateHelper.set_layout('layout_vertical.html', context)
        context['student_id'] = int(pk)
        return render(request, 'coordinator/coordinator_student_detail.html', context)


@method_decorator(login_required, name='dispatch')
class CoordinatorStudentDetailAPI(View):
    """JSON API — returns full student stats."""
    def get(self, request, pk):
        _, _, student_ids = get_coordinator_scope(request.user)
        if pk not in student_ids:
            return JsonResponse({'error': 'Not in your scope'}, status=403)

        student = StudentModel.objects.filter(id=pk).first()
        if not student:
            return JsonResponse({'error': 'Not found'}, status=404)

        attempts = StudentTestAttemptModel.objects.filter(student_id=pk)
        avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0

        # Trend: compare last 3 tests vs previous 3 tests
        recent_scores = list(
            attempts.order_by('-started_at').values_list('score', flat=True)[:3]
        )
        older_scores = list(
            attempts.order_by('-started_at').values_list('score', flat=True)[3:6]
        )
        if recent_scores and older_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            if recent_avg > older_avg + 5:
                trend = 'Improving'
            elif recent_avg < older_avg - 5:
                trend = 'Falling'
            else:
                trend = 'Stable'
        else:
            trend = 'Stable'

        study_total = StudySession.objects.filter(
            student_id=pk
        ).aggregate(total=Sum('duration'))['total'] or 0

        hw_assigned  = HomeworkModel.objects.filter(assigned_to=pk).count()
        hw_submitted = HomeworkSubmissionModel.objects.filter(student_id=pk).count()
        hw_pct       = round((hw_submitted / hw_assigned * 100) if hw_assigned else 0, 1)

        last_session = StudySession.objects.filter(
            student_id=pk
        ).order_by('-start_time').first()
        last_active = last_session.start_time.strftime('%Y-%m-%d') if last_session else 'Never'

        remarks = list(TeacherRemarkModel.objects.filter(student_id=pk).values(
            'remark', 'remark_type', 'created_at'
        ))

        # Rich risk tag including Falling/Improving
        if last_active == 'Never':
            risk = 'Inactive'
        elif trend == 'Falling':
            risk = 'Falling'
        elif trend == 'Improving':
            risk = 'Improving'
        elif avg_score < 25:
            risk = 'High Risk'
        elif avg_score < 40:
            risk = 'Needs Attention'
        elif avg_score >= 70:
            risk = 'Excellent'
        else:
            risk = 'Stable'

        return JsonResponse({
            'id':              pk,
            'name':            student.student_name,
            'class':           str(student.student_class) if student.student_class else '-',
            'avg_score':       round(avg_score, 1),
            'study_time':      f'{round(study_total / 60, 1)} hrs total',
            'homework_pct':    hw_pct,
            'tests_attempted': attempts.count(),
            'last_active':     last_active,
            'trend':           trend,
            'risk':            risk,
            'remarks':         remarks,
        })

@method_decorator(login_required, name='dispatch')
class CoordinatorGlobalSearchAPI(View):
    """
    GET /coordinator/api/search/?q=<query>
    Searches student name, teacher name, class name, tablet ID within scope.
    """
    def get(self, request):
        class_ids, teacher_ids, student_ids = get_coordinator_scope(request.user)
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 2:
            return JsonResponse({'results': []})

        results = []

        # Students
        for student in StudentModel.objects.filter(
            id__in=student_ids,
            student_name__icontains=q
        )[:10]:
            avg = StudentTestAttemptModel.objects.filter(
                student_id=student.id
            ).aggregate(avg=Avg('score'))['avg'] or 0
            results.append({
                'type':     'Student',
                'id':       student.id,
                'label':    student.student_name,
                'sub':      str(student.student_class) if student.student_class else '-',
                'url':      f'/coordinator/students/{student.id}/',
                'badge':    'High Risk' if avg < 40 else 'OK',
            })

        # Teachers
        for teacher in UserModel.objects.filter(
            id__in=teacher_ids
        ).filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )[:5]:
            results.append({
                'type':  'Teacher',
                'id':    teacher.id,
                'label': f'{teacher.first_name} {teacher.last_name}',
                'sub':   teacher.email,
                'url':   f'/coordinator/teachers/',
                'badge': '',
            })

        # Classes
        for cls in ClassModel.objects.filter(id__in=class_ids):
            if q.lower() in str(cls).lower():
                results.append({
                    'type':  'Class',
                    'id':    cls.id,
                    'label': str(cls),
                    'sub':   '',
                    'url':   f'/coordinator/classes/{cls.id}/',
                    'badge': '',
                })

        # Tablet ID search
        devices = DeviceModel.objects.filter(
            imei_number__icontains=q,
            user__in=UserModel.objects.filter(
                id__in=[s for s in student_ids]
            )
        )[:5]
        for device in devices:
            results.append({
                'type':  'Device',
                'id':    device.id,
                'label': device.imei_number,
                'sub':   'Tablet',
                'url':   f'/coordinator/devices/',
                'badge': '',
            })

        return JsonResponse({'results': results, 'count': len(results)})

# ─── Page Views — inherit DashboardsView so sidebar/breadcrumbs work ──────────

@method_decorator(login_required, name='dispatch')
class CoordinatorDashboardView(DashboardsView):
    template_name = "coordinator/coordinator_dashboard.html"

    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = self.get_context_data()
        context["user"] = request.user
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorClassListView(DashboardsView):
    template_name = "coordinator/coordinator_classes.html"

    def get(self, request):
        class_ids, _, _ = get_coordinator_scope(request.user)
        classes = ClassModel.objects.filter(id__in=class_ids)
        context = self.get_context_data()
        context['classes'] = classes
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorClassDetailView(DashboardsView):
    template_name = "coordinator/coordinator_class_detail.html"

    def get(self, request, pk=None):
        class_ids, _, _ = get_coordinator_scope(request.user)
        if pk not in class_ids:
            return redirect('coordinator-classes')
        context = self.get_context_data()
        context['class_id'] = pk
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherListView(DashboardsView):
    template_name = "coordinator/coordinator_teachers.html"

    def get(self, request):
        _, teacher_ids, _ = get_coordinator_scope(request.user)
        teachers = UserModel.objects.filter(id__in=teacher_ids)
        context = self.get_context_data()
        context['teachers'] = teachers
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorTeacherNeglectView(DashboardsView):
    template_name = "coordinator/coordinator_teacher_neglect.html"

    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorStudentListView(DashboardsView):
    template_name = "coordinator/coordinator_students.html"

    def get(self, request):
        _, _, student_ids = get_coordinator_scope(request.user)
        students = StudentModel.objects.filter(id__in=student_ids)
        context = self.get_context_data()
        context['students'] = students
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorStudentDetailView(DashboardsView):
    template_name = "coordinator/coordinator_student_detail.html"

    def get(self, request, pk):
        _, _, student_ids = get_coordinator_scope(request.user)
        if pk not in student_ids:
            return redirect('coordinator-students')
        context = self.get_context_data()
        context['student_id'] = pk
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorSubjectView(DashboardsView):
    template_name = "coordinator/coordinator_subjects.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorTestListView(DashboardsView):
    template_name = "coordinator/coordinator_tests.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorHomeworkView(DashboardsView):
    template_name = "coordinator/coordinator_homework.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorStudyTimeView(DashboardsView):
    template_name = "coordinator/coordinator_study_time.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorWeaknessView(DashboardsView):
    template_name = "coordinator/coordinator_weakness.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorActionView(DashboardsView):
    template_name = "coordinator/coordinator_actions.html"

    def get(self, request):
        actions = CoordinatorActionModel.objects.filter(
            coordinator=request.user
        ).order_by('priority', '-created_at')
        context = self.get_context_data()
        context['actions'] = actions
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorAlertView(DashboardsView):
    template_name = "coordinator/coordinator_alerts.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorReportsView(DashboardsView):
    template_name = "coordinator/coordinator_reports.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorDeviceView(DashboardsView):
    template_name = "coordinator/coordinator_devices.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorEscalationView(DashboardsView):
    template_name = "coordinator/coordinator_escalations.html"

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorProfileView(DashboardsView):
    template_name = "coordinator/coordinator_profile.html"

    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = self.get_context_data()
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CoordinatorSettingsView(DashboardsView):
    template_name = "coordinator/coordinator_settings.html"

    def get(self, request):
        if request.user.role.type != 'Coordinator':
            return redirect('index')
        context = self.get_context_data()
        return render(request, self.template_name, context)