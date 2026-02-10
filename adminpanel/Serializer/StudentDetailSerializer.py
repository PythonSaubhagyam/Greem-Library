from rest_framework import serializers
from user_management.models import *
from tablet_app.models import *
from django.db import transaction

class pdfSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d at %H:%M:%S", read_only=True)

    class Meta:
        model = pdfLibraryModel
        fields = ['title', 'pdf_file', 'total_pages', 'group', 'is_custom', 'is_favorite', 'created_at']

class pdfGroupSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d at %H:%M:%S", read_only=True)
    pdfs_counts = serializers.SerializerMethodField()

    def get_pdfs_counts(self, obj):
        pdf_counts = obj.pdflibrarymodel_set.filter(student_id=self.context.get('student_id')).count()
        return pdf_counts

    class Meta:
        model = pdfGroupModel
        fields = ['id', 'name', 'created_at', 'pdfs_counts']

class StudentTestAttemptSerializer(serializers.ModelSerializer):

    test_title = serializers.CharField(source="test.title")
    number_of_questions = serializers.IntegerField(source="test.number_of_questions")
    question_type = serializers.CharField(source="test.question_type")
    total_marks = serializers.IntegerField(source="test.total_marks")
    duration_minutes = serializers.IntegerField(source="test.duration_minutes")

    started_at = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()

    class Meta:
        model = StudentTestAttemptModel
        fields = [
            "id",
            "test_title",
            "number_of_questions",
            "question_type",
            "total_marks",
            "duration_minutes",
            "score",
            "started_at",
            "completed_at",
            "is_completes",
        ]

    def get_started_at(self, obj):
        return timezone.localtime(obj.started_at).strftime("%Y-%m-%d at %H:%M:%S")

    def get_completed_at(self, obj):
        return (
            timezone.localtime(obj.completed_at).strftime("%Y-%m-%d at %H:%M:%S")
            if obj.completed_at else None
        )