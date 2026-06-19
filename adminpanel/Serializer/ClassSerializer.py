from rest_framework import serializers

try:
    from user_management.models import ClassModel
except Exception:
    ClassModel = None


class ClassSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = ClassModel
        fields = [
            'id', 'standard', 'section', 'academic_year',
            'is_active', 'created_at', 'student_count'
        ]

    def get_student_count(self, obj):
        try:
            return obj.students.count()
        except Exception:
            return 0
