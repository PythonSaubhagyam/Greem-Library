from rest_framework import serializers
from tablet_app.models import (
    pdfGroupModel, pdfLibraryModel, Subject,
    TestModel, QuestionsModel, QuestionOptionsModel,
    StudentTestAttemptModel, StudentAnswerModel,
    StudySession, StudentGroupModel, ReportModel)
from user_management.models import StudentModel, UserModel
from rest_framework import serializers
from tablet_app.models import (StudentGroupModel, Subject, TestModel)
from user_management.models import (StudentModel, UserModel,HomeworkModel, NotificationPreferenceModel)
from django.db.models import Avg, Count, Q
from django.utils import timezone
 

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


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportModel
        fields = '__all__'
        read_only_fields = ['created_at']




class HomeworkCreateSerializer(serializers.ModelSerializer):
    """Create homework — optionally assign to a group at creation time."""
 
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        source='subject',
        write_only=True,
        required=False,
        allow_null=True
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroupModel.objects.all(),
        source='group',
        write_only=True,
        required=False,
        allow_null=True
    )
    due_date = serializers.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],
        required=False
    )

 
    class Meta:
        model = HomeworkModel
        fields = [
            'id', 'title', 'subject_id', 'description',
            'due_date', 'total_marks', 'group_id'
        ]
        read_only_fields = ['id']
 
    def create(self, validated_data):
        group = validated_data.pop('group', None)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
 
        homework = HomeworkModel.objects.create(**validated_data)
 
        # If a group was provided, assign all students in that group
        if group:
            homework.group = group
            student_ids = group.students.values_list('id', flat=True)
            homework.assigned_to.set(student_ids)
            homework.save()
 
        return homework
 
 
class HomeworkAssignToGroupSerializer(serializers.Serializer):
    """
    Assign an EXISTING homework to a group.
    POST /api/homework/<homework_id>/assign-group/
    Body: { "group_id": 3 }
    """
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroupModel.objects.all()
    )
 
    def save(self, homework):
        group = self.validated_data['group_id']
        student_ids = group.students.values_list('id', flat=True)
        # Add group students (don't replace existing individual assignments)
        homework.assigned_to.add(*student_ids)
        homework.group = group
        homework.save()
        return homework
 
 
class HomeworkDetailSerializer(serializers.ModelSerializer):
    subject     = serializers.StringRelatedField(read_only=True)
    group_name  = serializers.SerializerMethodField()
    assigned_count = serializers.SerializerMethodField()
 
    class Meta:
        model = HomeworkModel
        fields = [
            'id', 'title', 'subject', 'description',
            'due_date', 'total_marks', 'group_name',
            'assigned_count', 'created_at'
        ]
 
    def get_group_name(self, obj):
        return obj.group.name if obj.group else None
 
    def get_assigned_count(self, obj):
        return obj.assigned_to.count()
 
 
# ------------------------------------------------------------
# SUGGESTED TEST SERIALIZER  (with real recommendation logic)
# ------------------------------------------------------------
 
class SuggestedTestSerializer(serializers.Serializer):
    """
    GET /api/groups/<group_id>/suggested-tests/
    Returns tests recommended for the group based on:
    - Subjects the group is weak in (avg score < 60%)
    - Tests not yet attempted by most group members
    """
    group_id = serializers.IntegerField(read_only=True)
    group_name = serializers.CharField(read_only=True)
    suggestions = serializers.ListField(read_only=True)
 
    @staticmethod
    def get_suggestions(group_id):
        try:
            group = StudentGroupModel.objects.prefetch_related('students').get(id=group_id)
        except StudentGroupModel.DoesNotExist:
            return None
 
        student_ids = list(group.students.values_list('id', flat=True))
        if not student_ids:
            return {
                'group_id': group_id,
                'group_name': group.name,
                'suggestions': [],
                'reason': 'No students in group'
            }
 
        # ── 1. Find weak subjects (avg score < 60%) ──────────────────
        from tablet_app.models import StudentTestAttemptModel
        attempts = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids
        ).values('test__subject__id', 'test__subject__name').annotate(
            avg_score=Avg('score'),
            attempt_count=Count('id')
        )
 
        weak_subject_ids = [
            a['test__subject__id']
            for a in attempts
            if a['avg_score'] is not None and a['avg_score'] < 60
        ]
 
        # ── 2. Find tests already attempted by >50% of group ─────────
        already_attempted = StudentTestAttemptModel.objects.filter(
            student_id__in=student_ids
        ).values('test_id').annotate(
            attempt_count=Count('student_id', distinct=True)
        ).filter(
            attempt_count__gte=len(student_ids) * 0.5
        ).values_list('test_id', flat=True)
 
        # ── 3. Build recommended tests ────────────────────────────────
        recommended_tests = TestModel.objects.filter(
            Q(subject_id__in=weak_subject_ids) | Q(subject__isnull=False)
        ).exclude(
            id__in=already_attempted
        ).select_related('subject')[:10]
 
        suggestions = []
        for test in recommended_tests:
            # Determine reason for suggestion
            if test.subject_id in weak_subject_ids:
                reason = f"Group is weak in {test.subject.name} (avg < 60%)"
                priority = "high"
            else:
                reason = "Not yet attempted by most group members"
                priority = "medium"
 
            suggestions.append({
                'test_id':    test.id,
                'title':      test.title,
                'subject':    test.subject.name if test.subject else None,
                'total_marks': test.total_marks,
                'questions':  test.number_of_questions,
                'reason':     reason,
                'priority':   priority,
            })
 
        # Sort: high priority first
        suggestions.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)
 
        return {
            'group_id':   group.id,
            'group_name': group.name,
            'student_count': len(student_ids),
            'suggestions': suggestions,
        }
 
 
# ------------------------------------------------------------
# NOTIFICATION PREFERENCE SERIALIZER
# ------------------------------------------------------------
 
class NotificationPreferenceSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = NotificationPreferenceModel
        fields = [
            'id',
            # Homework
            'homework_assigned', 'homework_due', 'homework_graded',
            # Test
            'test_scheduled', 'test_result',
            # Progress
            'goal_achieved', 'badge_earned', 'weekly_report',
            # Remarks
            'teacher_remark',
            # Channels
            'push_enabled', 'email_enabled', 'sms_enabled',
            'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']
 
