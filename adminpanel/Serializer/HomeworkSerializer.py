from rest_framework import serializers
from adminpanel.models import HomeworkModel, HomeworkSubmissionModel
from adminpanel.Serializer.StudentSerializer import StudentsSerializer

class HomeworkSerializer(serializers.ModelSerializer):
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    students = StudentsSerializer(many=True, read_only=True)

    class Meta:
        model = HomeworkModel
        fields = ['id','title','description','assigned_by','assigned_by_name','students','target_class','due_date','created_at']

class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = HomeworkSubmissionModel
        fields = ['id','homework','student','submitted_at','content','attachment','is_checked','checked_by','marks']
