from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Avg
from web_project import TemplateLayout, TemplateHelper

from adminpanel.views import DashboardsView
from user_management.models import StudentModel, ClassModel
from tablet_app.models import StudentTestAttemptModel, Subject


@method_decorator(login_required, name='dispatch')
class WeaknessAnalysisView(DashboardsView):
    template_name = "weakness_analysis.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })

        user = request.user
        students = StudentModel.objects.filter(parent=user)
        student_ids = list(students.values_list('id', flat=True))

        # Weak Students (avg score < 40)
        weak_students = []
        for student in students.select_related('student_class'):
            attempts = StudentTestAttemptModel.objects.filter(student=student)
            if not attempts.exists():
                continue
            avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            if avg_score < 40:
                weak_students.append({
                    'name': student.student_name,
                    'class': str(student.student_class) if student.student_class else '—',
                    'avg_score': round(avg_score, 1),
                    'tests_taken': attempts.count(),
                    'risk': 'High Risk' if avg_score < 25 else 'Needs Attention',
                })

        # Weak Classes
        weak_classes = []
        classes = ClassModel.objects.filter(students__in=student_ids).distinct()
        for cls in classes:
            cls_student_ids = cls.students.filter(
                id__in=student_ids
            ).values_list('id', flat=True)
            attempts = StudentTestAttemptModel.objects.filter(student__in=cls_student_ids)
            if not attempts.exists():
                continue
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            if avg < 50:
                weak_classes.append({
                    'name': str(cls),
                    'avg_score': round(avg, 1),
                    'student_count': len(cls_student_ids),
                    'status': 'Critical' if avg < 30 else 'Weak',
                })

        # Weak Subjects
        weak_subjects = []
        for subject in Subject.objects.all():
            attempts = StudentTestAttemptModel.objects.filter(
                student__in=student_ids,
                test__subject=subject
            )
            if not attempts.exists():
                continue
            avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
            if avg < 50:
                weak_subjects.append({
                    'name': subject.name,
                    'avg_score': round(avg, 1),
                    'weak_students': attempts.filter(score__lt=40).count(),
                    'status': 'Critical' if avg < 30 else 'Weak',
                })

        context.update({
            'weak_students': weak_students,
            'weak_classes': weak_classes,
            'weak_subjects': weak_subjects,
            'total_weak_students': len(weak_students),
            'total_weak_classes': len(weak_classes),
            'total_weak_subjects': len(weak_subjects),
            'total_students': students.count(),
        })

        return render(request, self.template_name, context)