from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from web_project import TemplateHelper

from adminpanel.views import DashboardsView
from user_management.models import StudentModel, ClassModel
from tablet_app.models import (
    StudentTestAttemptModel,
    StudySession,
    Subject,
)
from adminpanel.models import HomeworkModel, HomeworkSubmissionModel


@method_decorator(login_required, name='dispatch')
class AlertsView(DashboardsView):
    template_name = "alerts.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })

        user = request.user
        students = StudentModel.objects.filter(parent=user)
        student_ids = list(students.values_list('id', flat=True))

        today = timezone.now().date()
        three_days_ago = today - timedelta(days=3)
        seven_days_ago = today - timedelta(days=7)

        high_alerts = []
        medium_alerts = []
        low_alerts = []

        # --- HIGH: Student score below 40% ---
        for student in students.select_related('student_class'):
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            if not attempts.exists():
                continue
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            if avg < 40:
                high_alerts.append({
                    'icon': 'bx-trending-down',
                    'color': 'danger',
                    'title': f"{student.student_name} score below 40%",
                    'detail': f"Avg score: {round(avg, 1)}% | Class: {student.student_class or '—'}",
                    'action': 'Contact teacher for follow-up',
                    'priority': 'High',
                })

        # --- HIGH: Student inactive for 3+ days ---
        inactive_students = []
        for student in students:
            last_session = StudySession.objects.filter(
                student=student
            ).order_by('-end_time').first()
            if not last_session:
                inactive_students.append(student.student_name)
                continue
            if last_session.end_time.date() < three_days_ago:
                inactive_students.append(student.student_name)

        if inactive_students:
            high_alerts.append({
                'icon': 'bx-user-x',
                'color': 'danger',
                'title': f"{len(inactive_students)} student(s) inactive for 3+ days",
                'detail': ', '.join(inactive_students[:5]),
                'action': 'Check device usage and follow up',
                'priority': 'High',
            })

        # --- MEDIUM: Homework pending above 50% ---
        homeworks = HomeworkModel.objects.filter(
            students__in=student_ids
        ).distinct()
        for hw in homeworks:
            assigned = hw.students.filter(id__in=student_ids).count()
            if assigned == 0:
                continue
            submitted = HomeworkSubmissionModel.objects.filter(
                homework=hw,
                student__in=student_ids
            ).count()
            pending = assigned - submitted
            pending_pct = (pending / assigned) * 100
            if pending_pct > 50:
                medium_alerts.append({
                    'icon': 'bx-book-open',
                    'color': 'warning',
                    'title': f"Homework '{hw.title}' pending {round(pending_pct)}%",
                    'detail': f"{pending}/{assigned} students not submitted",
                    'action': 'Follow up with students',
                    'priority': 'Medium',
                })

        # --- MEDIUM: No test taken in 7 days ---
        from tablet_app.models import TestModel
        recent_test = StudentTestAttemptModel.objects.filter(
            student__in=student_ids,
            started_at__date__gte=seven_days_ago
        ).exists()
        if not recent_test:
            medium_alerts.append({
                'icon': 'bx-clipboard',
                'color': 'warning',
                'title': 'No tests taken in last 7 days',
                'detail': 'Students have not attempted any test this week',
                'action': 'Ask teacher to schedule a test',
                'priority': 'Medium',
            })

        # --- MEDIUM: Weak subject detected ---
        for subject in Subject.objects.all():
            attempts = StudentTestAttemptModel.objects.filter(
                student__in=student_ids,
                test__subject=subject
            )
            if not attempts.exists():
                continue
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            if avg < 40:
                medium_alerts.append({
                    'icon': 'bx-book-alt',
                    'color': 'warning',
                    'title': f"Weak subject detected: {subject.name}",
                    'detail': f"Average score: {round(avg, 1)}%",
                    'action': 'Schedule revision for this subject',
                    'priority': 'Medium',
                })

        # --- LOW: No study session today ---
        active_today = StudySession.objects.filter(
            student__in=student_ids,
            start_time__date=today
        ).values_list('student_id', flat=True).distinct()
        not_active_today = students.exclude(id__in=active_today)
        if not_active_today.exists():
            low_alerts.append({
                'icon': 'bx-time',
                'color': 'info',
                'title': f"{not_active_today.count()} student(s) not active today",
                'detail': ', '.join(
                    [s.student_name for s in not_active_today[:5]]
                ),
                'action': 'Check tablet usage',
                'priority': 'Low',
            })

        total_alerts = len(high_alerts) + len(medium_alerts) + len(low_alerts)

        context.update({
            'high_alerts': high_alerts,
            'medium_alerts': medium_alerts,
            'low_alerts': low_alerts,
            'total_alerts': total_alerts,
            'high_count': len(high_alerts),
            'medium_count': len(medium_alerts),
            'low_count': len(low_alerts),
        })

        return render(request, self.template_name, context)