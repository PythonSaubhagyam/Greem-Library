from rest_framework import serializers
from tablet_app.models import TestModel, QuestionsModel, QuestionOptionsModel, StudentTestAttemptModel
from adminpanel.Serializer.StudentSerializer import StudentsSerializer

class QuestionOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOptionsModel
        fields = ['id', 'option_text', 'is_correct']

class QuestionsSerializer(serializers.ModelSerializer):
    options = QuestionOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionsModel
        fields = ['id', 'question_text', 'marks', 'options']

class TestSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    questions = QuestionsSerializer(many=True, read_only=True)
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = TestModel
        fields = [
            'id', 'title', 'subject', 'subject_name', 'number_of_questions',
            'question_type', 'duration_minutes', 'total_marks', 'shuffle_questions',
            'enable_timer', 'created_at', 'scheduled_date', 'created_by',
            'created_by_name', 'questions', 'students_count'
        ]

    def get_students_count(self, obj):
        return obj.student.count()

class StudentTestAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    test_title = serializers.CharField(source='test.title', read_only=True)

    class Meta:
        model = StudentTestAttemptModel
        fields = ['id', 'student', 'student_name', 'test', 'test_title', 'score', 'started_at', 'completed_at', 'is_completes']
