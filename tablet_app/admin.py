from django.contrib import admin
from tablet_app.models import *

# Register your models here.


@admin.register(pdfGroupModel)
class pdfGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at','updated_at')
    search_fields = ('name',)
    ordering = ("-id",)


@admin.register(pdfLibraryModel)
class pdfLibraryAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'pdf_file', 'total_pages', 'is_custom', 'is_favorite', 'student', 'created_at', 'updated_at')
    search_fields = ('title', 'pdf_file', 'created_at', 'updated_at')
    ordering = ("-id",)
    filter_horizontal = ("group",)


@admin.register(TestModel)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'number_of_questions', 'question_type', 'duration_minutes', 'total_marks', 
                    'shuffle_questions','enable_timer', 'created_at')
    search_fields = ('title', 'question_type', 'shuffle_questions', 'enable_timer','created_by__email', 'created_at',)
    filter_horizontal = ("pdf", 'student',)
    ordering = ("-id",)


@admin.register(QuestionsModel)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'question_text', 'marks')
    search_fields = ('question_text', 'marks',)
    ordering = ('-id',)


@admin.register(QuestionOptionsModel)
class QuestionOptionsAdmin(admin.ModelAdmin):
    list_display = ('question', 'option_text', 'is_correct')
    search_fields = ('option_text', 'is_correct',)
    ordering = ('-id',)


@admin.register(StudentTestAttemptModel)
class StudentTestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'started_at', 'completed_at', 'is_completes')
    search_fields = ('score', 'started_at', 'completed_at', 'is_completes',)
    ordering = ('-id',)


@admin.register(StudentAnswerModel)
class StudentAnswer(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option')
    search_fields = ('attempt', 'question', 'selected_option',)
    ordering = ('-id',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id','name',)
    search_fields = ('name',)
    ordering = ("-id",)

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'start_time', 'end_time', 'duration')
    search_fields = ('student__name', 'subject__name',)
    ordering = ("-id",)

@admin.register(StudentGroupModel)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by_name', 'subject', 'class_display', 'get_student_count', 'created_at')
    search_fields = ('name', 'description', 'created_by__first_name', 'created_by__last_name')
    list_filter = ('subject', 'class_ref__standard', 'class_ref__section', 'created_at')
    filter_horizontal = ('students',)
    raw_id_fields = ('created_by', 'subject', 'class_ref')
    ordering = ("-id",)

    fieldsets = (
        ("Group Information", {
            "fields": ("name", "description", "created_by")
        }),
        ("Classification", {
            "fields": ("class_ref", "subject")
        }),
        ("Students", {
            "fields": ("students",)
        }),
    )

    def get_student_count(self, obj):
        return obj.students.count()
    get_student_count.short_description = 'Student Count'

    def created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return "-"
    created_by_name.short_description = 'Created By'

    def class_display(self, obj):
        return str(obj.class_ref) if obj.class_ref else "-"
    class_display.short_description = 'Class'