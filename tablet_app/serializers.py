from rest_framework import serializers
from tablet_app.models import *


class pdfGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = pdfGroupModel
        fields = ['name', 'created_at']


class pdfLibrarySerializer(serializers.ModelSerializer):

    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=pdfGroupModel.objects.all(),
        many=True,
        source='group',
        write_only=True,
        required=False
    )
    
    group = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = pdfLibraryModel
        fields = ['title', 'pdf_file', 'total_pages', 'group_ids', 'group', 'is_custom', 'is_favorite', 'created_at']


    def create(self, validated_data):
        user = self.context['request'].user
        groups = validated_data.pop('group', [])

        pdf = pdfLibraryModel.objects.create(
            student=user,
            **validated_data
        )
        pdf.group.set(groups)
        return pdf

    
class TestSerializer(serializers.ModelSerializer):
    pdf_id = serializers.PrimaryKeyRelatedField(
        queryset=pdfLibraryModel.objects.all(),
        source='pdf',
        write_only=True
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all(),
        source='student',
        write_only=True
    )

    pdf = serializers.StringRelatedField(read_only=True)
    student = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TestModel
        fields = ['title', 'pdf_id', 'pdf', 'number_of_questions', 'question_type', 'duration_minutes', 'total_marks', 'shuffle_questions',
                  'enable_timer', 'student_id', 'student', 'created_at']
        

class QuestionsSerializer(serializers.ModelSerializer):
    test_id = serializers.PrimaryKeyRelatedField(
        queryset = TestModel.objects.all(),
        source = 'test',
        write_only = True
    )

    test = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuestionsModel
        fields = ['test_id', 'test', 'question_text', 'marks']


class QuestionOptionsSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset = QuestionsModel.objects.all(),
        source = 'question',
        write_only=True
    )

    question = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = QuestionOptionsModel
        fields = ['question_id', 'question', 'option_text', 'is_correct']


class StudentTestAttemptSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset = UserModel.objects.all(),
        source = 'student',
        write_only = True,
        required=False
    )
    test_id = serializers.PrimaryKeyRelatedField(
        queryset = TestModel.objects.all(),
        source = 'test',
        write_only = True
    )

    student = serializers.StringRelatedField(read_only=True)
    test = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StudentTestAttemptModel
        fields = ['student_id', 'student', 'test_id', 'test', 'score', 'started_at', 'completed_at', 'is_completes']
        read_only_fields = ['score', 'started_at', 'completed_at', 'is_completes']


class StudentAnswerSerializer(serializers.ModelSerializer):
    attempt_id = serializers.PrimaryKeyRelatedField(
        queryset = StudentTestAttemptModel.objects.all(),
        source = 'attempt',
        write_only = True
    )
    question_id = serializers.PrimaryKeyRelatedField(
        queryset = QuestionsModel.objects.all(),
        source = 'question',
        write_only = True
    )
    selected_option_id = serializers.PrimaryKeyRelatedField(
        queryset = QuestionOptionsModel.objects.all(),
        source = 'selected_option',
        write_only = True
    )

    attempt = serializers.StringRelatedField(read_only=True)
    question = serializers.StringRelatedField(read_only=True)
    selected_option = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StudentAnswerModel
        fields = ['attempt_id', 'attempt', 'question_id', 'question', 'selected_option_id', 'selected_option']