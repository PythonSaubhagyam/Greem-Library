from rest_framework import serializers
from user_management.models import UserModel
from tablet_app.models import TestModel, Subject
from adminpanel.models import HomeworkModel

class TeacherAnalyticsSerializer(serializers.Serializer):
    """Serializer for teacher analytics dashboard"""
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    subject = serializers.CharField()
    classes_assigned = serializers.IntegerField()
    classes_taken = serializers.IntegerField()
    tests_conducted = serializers.IntegerField()
    homework_given = serializers.IntegerField()
    homework_checked = serializers.IntegerField()
    avg_student_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    weak_students_count = serializers.IntegerField()
    last_active_date = serializers.DateTimeField(required=False, allow_null=True)
    accountability_score = serializers.DecimalField(max_digits=5, decimal_places=2)

class CoordinatorAnalyticsSerializer(serializers.Serializer):
    """Serializer for coordinator analytics dashboard"""
    coordinator_id = serializers.IntegerField()
    coordinator_name = serializers.CharField()
    classes_handled = serializers.IntegerField()
    teachers_under = serializers.IntegerField()
    students_under = serializers.IntegerField()
    weak_students_count = serializers.IntegerField()
    avg_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    teacher_activity_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    pending_actions = serializers.IntegerField()
    status = serializers.CharField()  # Good/Average/Weak/Critical
    control_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    has_neglect_alert = serializers.BooleanField()

class SubjectAnalyticsSerializer(serializers.Serializer):
    """Serializer for subject analytics"""
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    avg_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    weak_students_count = serializers.IntegerField()
    best_class = serializers.CharField(required=False, allow_null=True)
    weakest_class = serializers.CharField(required=False, allow_null=True)
    responsible_teachers = serializers.ListField(child=serializers.CharField())

class TestAnalyticsSerializer(serializers.Serializer):
    """Serializer for test analytics"""
    test_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    subject = serializers.CharField()
    class_name = serializers.CharField()
    date = serializers.DateTimeField()
    avg_marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    highest_marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    lowest_marks = serializers.DecimalField(max_digits=5, decimal_places=2)
    students_absent = serializers.IntegerField()
    students_failed = serializers.IntegerField()
    students_passed = serializers.IntegerField()
    retest_needed = serializers.BooleanField()

class HomeworkAnalyticsSerializer(serializers.Serializer):
    """Serializer for homework analytics"""
    homework_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    subject = serializers.CharField()
    class_name = serializers.CharField()
    assigned_count = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    checked_count = serializers.IntegerField()
    feedback_given = serializers.BooleanField()
    status = serializers.CharField()  # Good/Average/Bad
