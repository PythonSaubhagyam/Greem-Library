from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from web_project import TemplateHelper
from adminpanel.views import DashboardsView
from user_management.models import UserModel, StudentModel, ClassModel
from django.db.models import Avg


@method_decorator(login_required, name='dispatch')
class CoordinatorsView(DashboardsView):
    template_name = "coordinators_list.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
        })

        user = request.user

        # ✅ FIX: Get coordinators by role name = 'Coordinator'
        # and same firm/school as the logged-in customer (principal)
        # firm = getattr(user, 'firm_name', None)

        coordinators_qs = UserModel.objects.filter(
            role__name__iexact='Coordinator'
        )
        print("Coordinator count:", coordinators_qs.count())

        # # ✅ Filter by same school/firm if firm_name exists
        # if firm:
        #     coordinators_qs = coordinators_qs.filter(firm_name__iexact=firm)

        coordinators_data = []

        for coord in coordinators_qs:

            # Classes under this coordinator
            try:
                classes = ClassModel.objects.filter(
                    coordinator_managed_classes__coordinator=coord
                ).distinct()
            except Exception:
                classes = ClassModel.objects.none()

            # Teachers under coordinator
            try:
                teachers = UserModel.objects.filter(
                    managed_by_coordinator__coordinator=coord,
                    role__name__iexact='Teacher'
                ).distinct()
            except Exception:
                teachers = UserModel.objects.none()

            # Students under coordinator's classes
            try:
                class_ids = classes.values_list('id', flat=True)
                students = StudentModel.objects.filter(
                    student_class__in=class_ids
                ).distinct()
            except Exception:
                students = StudentModel.objects.none()

            # Weak students (avg score < 40%)
            weak_count = 0
            try:
                from tablet_app.models import StudentTestAttemptModel
                for student in students:
                    attempts = StudentTestAttemptModel.objects.filter(student=student)
                    if attempts.exists():
                        avg = attempts.aggregate(avg=Avg('score'))['avg'] or 0
                        if avg < 40:
                            weak_count += 1
            except Exception:
                weak_count = 0

            # Classes display string
            class_names = ', '.join([str(c) for c in classes[:3]])
            if classes.count() > 3:
                class_names += f' +{classes.count() - 3} more'

            coordinators_data.append({
                'id': coord.id,
                'name': f"{coord.first_name} {coord.last_name}".strip() or coord.email,
                'email': coord.email,
                'mobile': getattr(coord, 'mobile_no', None) or '—',
                'classes_count': classes.count(),
                'classes': class_names,
                'teachers_count': teachers.count(),
                'students_count': students.count(),
                'weak_students': weak_count,
                'is_active': coord.is_active,
            })

        context.update({
            'coordinators': coordinators_data,
            'total_coordinators': len(coordinators_data),
        })
        return render(request, self.template_name, context)