from rest_framework import serializers
from tablet_app.models import *


class pdfGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = pdfGroupModel
        fields = ['id','name', 'created_at','updated_at']
        read_only_fields = ['created_at', 'updated_at']


class StudentGroupSerializer(serializers.ModelSerializer):
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=StudentModel.objects.all(),
        many=True,
        source='students',
        write_only=True,
        required=False
    )

    students = serializers.SerializerMethodField(read_only=True)
    student_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentGroupModel
        fields = ['id', 'name', 'student_ids', 'students', 'student_count']

    def get_students(self, obj):
        return [
            {
                'id': student.id,
                'name': student.student_name,
                'email': student.email,
                'class': student.student_class
            }
            for student in obj.students.all()
        ]

    def get_student_count(self, obj):
        return obj.students.count()

    def create(self, validated_data):
        students = validated_data.pop('students', [])
        group = StudentGroupModel.objects.create(**validated_data)
        group.students.set(students)
        return group

    def update(self, instance, validated_data):
        students = validated_data.pop('students', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        if students is not None:
            instance.students.set(students)

        return instance


class pdfLibrarySerializer(serializers.ModelSerializer):
    student_id = serializers.CharField()

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
        fields = ['title', 'pdf_file', 'total_pages', 'group_ids', 'group', 'is_custom', 'is_favorite', 'created_at', 'updated_at', 'student','student_id']
        # read_only_fields = ['created_at', 'updated_at']


    def create(self, validated_data):
        # user = self.context['request'].user
        print(validated_data,'------------------')
        groups = validated_data.pop('group', [])
        print(groups,'-------------')
        device_id = validated_data.pop('student_id')
        print(device_id,'------------------')
        try :

          student = StudentModel.objects.get(device_id__imei_number=device_id)

        except StudentModel.DoesNotExist:
          raise serializers.ValidationError({'student_id': 'Invalid student_id'})

        validated_data['student'] = student

        pdf = pdfLibraryModel.objects.create(
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


class StudySessionSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentModel.objects.all(),
        source='student',
        write_only=True
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        source='subject',
        write_only=True,
        required=False,
        allow_null=True
    )

    student = serializers.SerializerMethodField(read_only=True)
    subject = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StudySession
        fields = [
            'id', 'student_id', 'student', 'subject_id', 'subject',
            'start_time', 'end_time', 'duration', 'interaction_count', 'is_active'
        ]
        read_only_fields = ['id', 'duration']

    def get_student(self, obj):
        return {
            'id': obj.student.id,
            'name': obj.student.student_name,
            'email': obj.student.email
        }