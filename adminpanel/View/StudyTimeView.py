from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum
from django.utils import timezone
from web_project import TemplateLayout, TemplateHelper

from adminpanel.views import DashboardsView
from user_management.models import StudentModel
from tablet_app.models import (
    pdfLibraryModel,
    pdfGroupModel,
    TestModel,
    StudentTestAttemptModel,
    StudySession,
)


@method_decorator(login_required, name='dispatch')
class StudyTimeView(DashboardsView):
    template_name = "study_time.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })

        user = request.user
        students = StudentModel.objects.filter(parent=user)
        student_ids = list(students.values_list('id', flat=True))

        total_pdfs = pdfLibraryModel.objects.filter(
            student__in=student_ids
        ).count()

        total_groups = pdfGroupModel.objects.filter(
            pdflibrarymodel__student__in=student_ids
        ).distinct().count()

        tests_taken = StudentTestAttemptModel.objects.filter(
            student__in=student_ids
        ).count()

        completed_tests = StudentTestAttemptModel.objects.filter(
            student__in=student_ids,
            is_completes=True
        ).count()

        today = timezone.now().date()
        study_minutes = StudySession.objects.filter(
            student__in=student_ids,
            start_time__date=today
        ).aggregate(total=Sum('duration'))['total'] or 0

        pdfs = pdfLibraryModel.objects.filter(
            student__in=student_ids
        ).order_by("-created_at")

        pdf_groups = pdfGroupModel.objects.filter(
            pdflibrarymodel__student__in=student_ids
        ).distinct().order_by("-created_at")

        tests = TestModel.objects.filter(
            student__in=student_ids
        ).order_by("-created_at")

        context.update({
            "total_pdfs": total_pdfs,
            "total_groups": total_groups,
            "tests_taken": tests_taken,
            "completed_tests": completed_tests,
            "incomplete_tests": tests_taken - completed_tests,
            "study_hours_today": round(study_minutes / 60, 1),
            "pdfs": pdfs,
            "pdf_groups": pdf_groups,
            "tests": tests,
        })

        return render(request, self.template_name, context)