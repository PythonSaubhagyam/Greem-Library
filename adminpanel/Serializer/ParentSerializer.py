
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from collections import defaultdict
from tablet_app.models import (
    StudySession, StudentTestAttemptModel, Subject, TestModel
)
from user_management.models import (
    StudentModel, UserModel,
    BadgeModel, StudentBadgeModel,
    LearningStyleModel,
    RewardModel, StudentRewardModel,
    StudentGoalModel,
)
import json
 
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
 
 
# =============================================================================
# SERIALIZERS
# =============================================================================
 
class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadgeModel
        fields = ['id', 'name', 'description', 'badge_type', 'icon',
                  'threshold', 'subject', 'is_active']
 
 
class StudentBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    subject_name = serializers.SerializerMethodField()
 
    class Meta:
        model = StudentBadgeModel
        fields = ['id', 'badge', 'earned_at', 'context', 'subject_name']
 
    def get_subject_name(self, obj):
        if obj.badge and obj.badge.subject:
            return obj.badge.subject.name
        return None
 
 
class LearningStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningStyleModel
        fields = ['style', 'visual_score', 'reading_score', 'practice_score',
                  'confidence', 'last_calculated', 'data_points']
 
 
class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardModel
        fields = ['id', 'name', 'description', 'reward_type', 'icon',
                  'min_score', 'max_score']
 
 
class StudentGoalSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
 
    class Meta:
        model = StudentGoalModel
        fields = ['id', 'student', 'student_name', 'goal_type', 'target_value',
                  'current_value', 'subject', 'subject_name', 'deadline',
                  'is_achieved', 'created_at', 'updated_at']
 
    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None
 
    def get_student_name(self, obj):
        return obj.student.student_name
 