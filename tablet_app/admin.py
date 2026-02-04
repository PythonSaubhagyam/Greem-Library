from django.contrib import admin
from tablet_app.models import *

# Register your models here.


@admin.register(pdfGroupModel)
class pdfGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ("-id",)


@admin.register(pdfLibraryModel)
class pdfLibraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'pdf_file', 'total_pages', 'is_custom', 'is_favorite', 'student', 'created_at')
    search_fields = ('title', 'pdf_file', 'created_at', )
    ordering = ("-id",)


@admin.register(TestModel)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'pdf', 'number_of_questions', 'question_type', 'duration_minutes', 'total_marks', 
                    'shuffle_questions','enable_timer', 'student', 'created_at')
    search_fields = ('title', 'question_type', 'shuffle_questions', 'enable_timer',)
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