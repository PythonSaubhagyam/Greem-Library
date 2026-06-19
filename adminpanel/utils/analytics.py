from django.db.models import Avg, Sum, Count, Q
from user_management.models import *
from tablet_app.models import *
from django.utils import timezone
from datetime import timedelta

def calculate_student_learning_score(student_id):
    """
    Formula: (Average Test Score * 0.6) + (Study Time Factor * 0.4)
    """
    student = StudentModel.objects.get(id=student_id)
    
    # Average Test Score
    avg_score = StudentTestAttemptModel.objects.filter(
        student=student, 
        is_completes=True
    ).aggregate(avg=Avg('score'))['avg'] or 0
    
    # Study Time Factor (Normalized: 10 hours/week = 100%)
    one_week_ago = timezone.now() - timedelta(days=7)
    total_study_minutes = StudySession.objects.filter(
        student=student,
        start_time__gte=one_week_ago
    ).aggregate(total=Sum('duration'))['total'] or 0
    
    study_time_factor = min((total_study_minutes / 600) * 100, 100)
    
    sls = (avg_score * 0.6) + (study_time_factor * 0.4)
    return round(sls, 2)

def calculate_teacher_accountability_score(teacher_id):
    """
    Weighted Formula:
    - Classes: 20%
    - Teaching Time: 20%
    - Tests Conducted: 15%
    - Homework Given: 15%
    - Homework Checked: 15%
    - Improvement: 15%
    """
    teacher = UserModel.objects.get(id=teacher_id)
    assignment = TeacherAssignmentModel.objects.filter(teacher=teacher).first()
    
    if not assignment:
        return 0
    
    # 1. Classes Factor (Max 5 classes = 100%)
    class_count = assignment.assigned_classes.count()
    classes_factor = min((class_count / 5) * 100, 100)
    
    # 2. Teaching Time (Total minutes in sessions for assigned classes / 1000 mins)
    total_teaching_minutes = StudySession.objects.filter(
        student__student_class__in=assignment.assigned_classes.all()
    ).aggregate(total=Sum('duration'))['total'] or 0
    teaching_time_factor = min((total_teaching_minutes / 1000) * 100, 100)
    
    # 3. Tests Conducted
    tests_count = TestModel.objects.filter(created_by=teacher).count()
    tests_factor = min((tests_count / 10) * 100, 100)
    
    # 4. Homework Given
    hw_given = HomeworkModel.objects.filter(created_by=teacher).count()
    hw_factor = min((hw_given / 10) * 100, 100)
    
    # 5. Homework Checked (Submissions with scores / Total assigned)
    hw_checked = HomeworkSubmissionModel.objects.filter(
        homework__created_by=teacher, 
        score__isnull=False
    ).count()
    hw_total = HomeworkSubmissionModel.objects.filter(homework__created_by=teacher).count()
    hw_check_factor = (hw_checked / hw_total * 100) if hw_total > 0 else 0
    
    # 6. Improvement (Average SLS of students under this teacher)
    students = StudentModel.objects.filter(student_class__in=assignment.assigned_classes.all())
    avg_sls = sum([calculate_student_learning_score(s.id) for s in students]) / students.count() if students.exists() else 0
    
    tas = (classes_factor * 0.2) + (teaching_time_factor * 0.2) + (tests_factor * 0.15) + \
          (hw_factor * 0.15) + (hw_check_factor * 0.15) + (avg_sls * 0.15)
          
    return round(tas, 2)

def calculate_class_health_score(class_id):
    """Average SLS of all students in the class."""
    students = StudentModel.objects.filter(student_class_id=class_id)
    if not students.exists():
        return 0
    total_sls = sum([calculate_student_learning_score(s.id) for s in students])
    return round(total_sls / students.count(), 2)

def calculate_coordinator_control_score(coordinator_id):
    """Average TAS of all teachers managed by this coordinator."""
    mappings = CoordinatorTeacherMapping.objects.filter(coordinator_id=coordinator_id)
    if not mappings.exists():
        return 0
    total_tas = sum([calculate_teacher_accountability_score(m.teacher_id) for m in mappings])
    return round(total_tas / mappings.count(), 2)
