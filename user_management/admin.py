from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
# Register your models here.



class UserAdmin(BaseUserAdmin, ImportExportModelAdmin):
    model = UserModel
    list_display = ("id","mobile_no","email", "first_name", "last_name", "role", "is_active", "is_staff","profile_image")
    list_filter = ("is_active", "is_staff", "is_superuser", "role")
    search_fields = ("email", "first_name", "last_name", "mobile_no")
    ordering = ("-id",)
    filter_horizontal = ("address",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "mobile_no", "address","firm_name","token")}),
        ("Role & Status", {"fields": ("role", "approved_status")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )
    
@admin.register(RoleModel)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id","name","type")
    search_fields = ("name",)


@admin.register(CountryModel)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("country_name", "country_code", "currency", "calling_code")
    search_fields = ("country_name", "country_code")


@admin.register(CountryGroupModel)
class CountryGroupAdmin(admin.ModelAdmin):
    list_display = ("group_name",)
    filter_horizontal = ("countries",)


@admin.register(StatesModel)
class StatesAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name",)
    list_filter = ("country",)


@admin.register(CitiesModel)
class CitiesAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "country", "is_active")
    list_filter = ("is_active", "country", "state")
    search_fields = ("name",)


@admin.register(AddressModel)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id","full_name", "address_tags", "city", "state", "country","pincode", "is_default")
    search_fields = ("full_name", "street", "address", "landmark")
    list_filter = ("is_default", "country", "state", "city")

admin.site.register(UserModel, UserAdmin)


@admin.register(StudentModel)
class StudentAdmin(ImportExportModelAdmin):
    list_display = ("id", "device_imei", "student_name", "email", "class_display")
    search_fields = ("student_name", "email", "parent__email", "device_id__imei_number")
    filter_horizontal = ("parent",)
    # list_filter = ("student_class__standard", "student_class__section", "student_class__academic_year")
    list_filter = ("student_class",)
    # raw_id_fields = ("device_id", "student_class")

    def device_imei(self, obj):
        return obj.device_id.imei_number if obj.device_id else "-"

    def class_display(self, obj):
        return str(obj.student_class) if obj.student_class else "-"
    class_display.short_description = "Class"

@admin.register(EmployeeModel)
class EmployeeAdmin(ImportExportModelAdmin):
    list_display = ("id","employee_id", "email", "department",)
    search_fields = ("user__email", "email", "employee_id", "department",)
    list_filter = ("email", "employee_id",)

@admin.register(DeviceModel)
class DeviceAdmin(ImportExportModelAdmin):
    list_display = ("id","user", "imei_number",'is_active')
    search_fields = ("user__email", "imei_number",)
    list_filter = ("imei_number",)


@admin.register(ClassModel)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("id", "standard", "section", "academic_year", "student_count", "is_active", "created_at")
    search_fields = ("standard", "section", "academic_year")
    list_filter = ("standard", "academic_year", "is_active")
    ordering = ("-academic_year", "standard", "section")

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Total Students"


@admin.register(TeacherAssignmentModel)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "teacher_name", "teacher_role", "assigned_subjects_display", "assigned_classes_display", "homeroom_class", "is_active", "created_at")
    search_fields = ("teacher__first_name", "teacher__last_name", "teacher__email")
    list_filter = ("teacher_role", "is_active", "assigned_subjects", "assigned_classes")
    filter_horizontal = ("assigned_classes", "assigned_subjects")
    # raw_id_fields = ("teacher", "homeroom_class")
    ordering = ("-created_at",)

    fieldsets = (
        ("Teacher Information", {
            "fields": ("teacher", "teacher_role", "is_active")
        }),
        ("Assignments", {
            "fields": ("assigned_classes", "assigned_subjects")
        }),
        ("Homeroom (Class Teacher Only)", {
            "fields": ("homeroom_class",),
            "description": "Only applicable if teacher_role is 'class_teacher'"
        }),
    )

    def teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"
    teacher_name.short_description = "Teacher"

    def assigned_subjects_display(self, obj):
        subjects = obj.assigned_subjects.all()[:5]
        subject_names = [s.name for s in subjects]
        if obj.assigned_subjects.count() > 5:
            subject_names.append(f"... +{obj.assigned_subjects.count() - 5} more")
        return ", ".join(subject_names) if subject_names else "-"
    assigned_subjects_display.short_description = "Subjects"

    def assigned_classes_display(self, obj):
        classes = obj.assigned_classes.all()[:5]
        class_names = [str(c) for c in classes]
        if obj.assigned_classes.count() > 5:
            class_names.append(f"... +{obj.assigned_classes.count() - 5} more")
        return ", ".join(class_names) if class_names else "-"
    assigned_classes_display.short_description = "Classes"

@admin.register(TabletLeadModel)
class TabletLeadAdmin(ImportExportModelAdmin):
    list_display = ("id", "name", "mobile", "email", "customer_type", "school_name", "tablet_model", "tablet_variant", "quantity", 
                    "price_per_unit", "total_price", "demo_required", "demo_done", "demo_date", "stage", "payment_status", "delivery_date",
                    "created_by", "assigned_to", "comment", "is_deleted", "created_at", "updated_at")
    search_fields = ("name", "email", "mobile", "customer_type", "tablet_model", "payment_status", )
    list_filter = ("name", "email",)


@admin.register(TabletLeadFollowUpModel)
class TabletLeadFollowUpAdmin(ImportExportModelAdmin):
    list_display = ("tablet_lead", "followup_type", "followup_date", "comment", "followup_by", "stage_update", "next_followup_date", "created_at")
    search_fields = ("tablet_lead", "followup_type", "comment", "stage_update", )
    list_filter = ("followup_type", "stage_update",)


# ============================================================================
# NEW MODEL ADMINS - Phase 2
# ============================================================================

@admin.register(StudentGoalModel)
class StudentGoalAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "goal_type", "target_value", "current_value", "subject", "deadline", "is_achieved", "created_at")
    search_fields = ("student__student_name", "goal_type")
    list_filter = ("goal_type", "is_achieved", "subject")
    raw_id_fields = ("student", "created_by")


@admin.register(BatchModel)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "teacher", "timing", "student_class", "subject", "student_count", "is_active", "created_at")
    search_fields = ("name", "teacher__first_name", "teacher__last_name")
    list_filter = ("is_active", "student_class", "subject")
    filter_horizontal = ("students",)
    raw_id_fields = ("teacher",)

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Students"


@admin.register(HomeworkModel)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subject", "due_date", "batch", "total_marks", "assigned_count", "created_by", "created_at")
    search_fields = ("title", "subject__name", "created_by__first_name")
    list_filter = ("subject", "due_date", "batch")
    filter_horizontal = ("assigned_to",)
    raw_id_fields = ("created_by", "batch")

    def assigned_count(self, obj):
        return obj.assigned_to.count()
    assigned_count.short_description = "Assigned To"


@admin.register(HomeworkSubmissionModel)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "homework", "student", "submitted_at", "score", "is_late")
    search_fields = ("homework__title", "student__student_name")
    list_filter = ("is_late", "submitted_at")
    raw_id_fields = ("homework", "student")


@admin.register(TeacherRemarkModel)
class TeacherRemarkAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "teacher", "remark_type", "is_visible_to_parent", "created_at")
    search_fields = ("student__student_name", "teacher__first_name", "remark")
    list_filter = ("remark_type", "is_visible_to_parent", "created_at")
    raw_id_fields = ("student", "teacher")


@admin.register(AchievementModel)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "badge_icon", "criteria_type", "criteria_value")
    search_fields = ("name", "description")
    list_filter = ("criteria_type",)


@admin.register(StudentAchievementModel)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "achievement", "earned_at")
    search_fields = ("student__student_name", "achievement__name")
    list_filter = ("achievement", "earned_at")
    raw_id_fields = ("student", "achievement")


@admin.register(StudentBadgeModel)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "badge", "earned_at")
    search_fields = ("student__student_name", "badge__name")
    list_filter = ("badge", "earned_at")
    raw_id_fields = ("student", "badge")

@admin.register(PrincipalCoordinatorMapping)
class PrincipalCoordinatorMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "principal", "coordinator", "created_at")
    search_fields = ("principal__email", "coordinator__email")
    list_filter = ("created_at",)
    raw_id_fields = ("principal", "coordinator")

@admin.register(CoordinatorAssignmentModel)
class CoordinatorAssignmentModelAdmin(admin.ModelAdmin):
    list_display = ("id", "coordinator", "class_obj", "subject", "teacher", "created_at")
    search_fields = ("coordinator__email",)
    list_filter = ("created_at",)

    raw_id_fields = ("coordinator", "class_obj", "teacher", "subject")
@admin.register(CoordinatorEscalationModel)
class CoordinatorEscalationModelAdmin(admin.ModelAdmin):
    list_display = ("id","coordinator","title","priority","status","teacher","created_at")
    search_fields = ("coordinator__email","title","description")
    list_filter = ("priority","status","created_at")
    raw_id_fields = ("coordinator","teacher","student")

@admin.register(CoordinatorActionModel)
class CoordinatorActionModelAdmin(admin.ModelAdmin):
    list_display = ("id","coordinator","priority","status","due_date","created_at")
    search_fields = ("coordinator__email","issue","responsible")
    list_filter = ("priority","status","due_date","created_at")
    raw_id_fields = ("coordinator",)

@admin.register(DeviceQRCodeModel)
class DeviceQRCodeModelAdmin(admin.ModelAdmin):
    list_display = ("id", "device", "qr_data", "is_used", "created_at")
    search_fields = ("device__imei_number",)
    list_filter = ("created_at",)
    raw_id_fields = ("device",)