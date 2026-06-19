from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Avg, Sum
from django.utils import timezone
from web_project import TemplateHelper

from adminpanel.views import DashboardsView
from user_management.models import StudentModel, ClassModel
from tablet_app.models import (
    StudentTestAttemptModel,
    TestModel,
    StudySession,
    Subject,
)
# adminpanel has TWO homework models — use adminpanel ones
from adminpanel.models import HomeworkModel, HomeworkSubmissionModel


@method_decorator(login_required, name='dispatch')
class ReportsView(DashboardsView):
    template_name = "reports.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })

        user = request.user
        students = StudentModel.objects.filter(parent=user)
        student_ids = list(students.values_list('id', flat=True))

        # --- Student Performance Report ---
        student_report = []
        for student in students.select_related('student_class'):
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0

            # adminpanel.HomeworkModel uses 'students' M2M
            hw_assigned = HomeworkModel.objects.filter(
                students=student
            ).count()
            hw_submitted = HomeworkSubmissionModel.objects.filter(
                student=student
            ).count()

            study_mins = StudySession.objects.filter(
                student=student
            ).aggregate(total=Sum('duration'))['total'] or 0

            student_report.append({
                'name': student.student_name,
                'class': str(student.student_class) if student.student_class else '—',
                'avg_score': round(avg_score, 1),
                'tests_taken': attempts.count(),
                'hw_completion': f"{hw_submitted}/{hw_assigned}",
                'study_hours': round(study_mins / 60, 1),
                'risk': (
                    'High Risk' if avg_score < 25 else
                    'Needs Attention' if avg_score < 40 else
                    'Stable'
                ),
            })

        # --- Class Report ---
        class_report = []
        classes = ClassModel.objects.filter(students__in=student_ids).distinct()
        for cls in classes:
            cls_ids = list(
                cls.students.filter(id__in=student_ids).values_list('id', flat=True)
            )
            attempts = StudentTestAttemptModel.objects.filter(student__in=cls_ids)
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            weak = 0
            for sid in cls_ids:
                s_avg = StudentTestAttemptModel.objects.filter(
                    student_id=sid
                ).aggregate(avg=Avg('score'))['avg'] or 100
                if s_avg < 40:
                    weak += 1

            class_report.append({
                'name': str(cls),
                'student_count': len(cls_ids),
                'avg_score': round(avg, 1),
                'weak_students': weak,
                'tests_count': TestModel.objects.filter(
                    student__in=cls_ids
                ).count(),
            })

        # --- Subject Report ---
        subject_report = []
        for subject in Subject.objects.all():
            attempts = StudentTestAttemptModel.objects.filter(
                student__in=student_ids,
                test__subject=subject
            )
            if not attempts.exists():
                continue
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            subject_report.append({
                'name': subject.name,
                'avg_score': round(avg, 1),
                'attempts': attempts.count(),
                'weak_students': attempts.filter(score__lt=40).count(),
            })

        # --- Test Report ---
        test_report = []
        tests = TestModel.objects.filter(
            student__in=student_ids
        ).select_related('subject').order_by('-created_at')[:20]
        for test in tests:
            attempts = StudentTestAttemptModel.objects.filter(test=test)
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            test_report.append({
                'title': test.title or '—',
                'subject': test.subject.name if test.subject else '—',
                'total_marks': test.total_marks,
                'attempts': attempts.count(),
                'avg_score': round(avg, 1),
                'completed': attempts.filter(is_completes=True).count(),
                'date': test.created_at.strftime('%d %b %Y'),
            })

        # --- Homework Report ---
        hw_report = []
        # adminpanel.HomeworkModel uses 'students' M2M
        homeworks = HomeworkModel.objects.filter(
            students__in=student_ids
        ).distinct().order_by('-created_at')[:20]

        for hw in homeworks:
            assigned = hw.students.filter(id__in=student_ids).count()
            submitted = HomeworkSubmissionModel.objects.filter(
                homework=hw,
                student__in=student_ids
            ).count()
            checked = HomeworkSubmissionModel.objects.filter(
                homework=hw,
                student__in=student_ids,
                is_checked=True
            ).count()
            pending = assigned - submitted
            hw_report.append({
                'title': hw.title,
                'due_date': hw.due_date.strftime('%d %b %Y') if hw.due_date else '—',
                'assigned': assigned,
                'submitted': submitted,
                'pending': pending,
                'checked': checked,
                'status': (
                    'Good' if pending == 0 else
                    'Bad' if pending > assigned // 2 else
                    'Average'
                ),
            })

        # --- Summary Stats ---
        overall_avg = StudentTestAttemptModel.objects.filter(
            student__in=student_ids
        ).aggregate(avg=Avg('score'))['avg'] or 0

        context.update({
            'total_students': students.count(),
            'total_tests': StudentTestAttemptModel.objects.filter(
                student__in=student_ids
            ).count(),
            'total_hw_assigned': HomeworkModel.objects.filter(
                students__in=student_ids
            ).distinct().count(),
            'total_hw_submitted': HomeworkSubmissionModel.objects.filter(
                student__in=student_ids
            ).count(),
            'overall_avg': round(overall_avg, 1),
            'student_report': student_report,
            'class_report': class_report,
            'subject_report': subject_report,
            'test_report': test_report,
            'hw_report': hw_report,
        })

        return render(request, self.template_name, context)