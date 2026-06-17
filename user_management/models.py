from django.db import models
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, Group, PermissionsMixin)
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from uuid import uuid4
from rest_framework.authtoken.models import Token
from tablet_app.models import *


# Create your models here.

class RoleModel(models.Model):
    name = models.CharField(max_length=150)
    type = models.CharField(choices=[('Admin','Admin'),('Teacher','Teacher'),('Parent','Parent'),('Employee','Employee'),('Customer','Customer'),('Coordinator','Coordinator')],max_length=100,null=True,blank=True)

    def __str__(self):
        return self.type
    
    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_role_name'),
            models.Index(fields=['type'], name='idx_role_type'),
        ]

class AccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        values = [email]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError("The {} value must be set".format(field_name))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        Token.objects.create(user=user)
        
        if extra_fields['is_superuser']:
            adminGroup, _ = Group.objects.get_or_create(name='Admin')
            adminGroup.user_set.add(user)
            
        return user
    

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        roles = RoleModel.objects.filter(type='Admin').first()
        if not roles:
            roles = RoleModel.objects.create(type='Admin',name='Admin')
        extra_fields.setdefault("role", roles)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

class CountryModel(models.Model):
    country_name = models.CharField(
        verbose_name='name', max_length=255, unique=True)
    country_code = models.CharField(verbose_name='country code', max_length=3)
    currency = models.CharField(max_length=3)
    calling_code = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'country'
        verbose_name_plural = 'countries'

    def __str__(self):
        return self.country_name


class CountryGroupModel(models.Model):
    group_name = models.CharField(max_length=255, verbose_name="group name")
    countries = models.ManyToManyField(CountryModel)

    class Meta:
        verbose_name = 'country group'
        verbose_name_plural = 'country groups'


class StatesModel(models.Model):
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CitiesModel(models.Model):
    country = models.ForeignKey(CountryModel, on_delete=models.CASCADE)
    state = models.ForeignKey(StatesModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class AddressModel(models.Model):
    address_types = (('Office', 'Office'),
                     ('Home', 'Home'), ('Other', 'Other'))
    full_name = models.CharField(max_length=255, blank=True, null=True)
    address_tags = models.CharField(
        choices=address_types, max_length=255, blank=True, null=True)
    mobile = PhoneNumberField(blank=True, null=True)
    another_mobile = PhoneNumberField(blank=True, null=True)
    street = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, verbose_name='pin code', blank=True, null=True)
    fcity = models.ForeignKey(CitiesModel, on_delete=models.SET_NULL, blank=True, null=True)
    fstate = models.ForeignKey(StatesModel, on_delete=models.SET_NULL, blank=True, null=True)
    fcountry = models.ForeignKey(CountryModel, on_delete=models.SET_NULL, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=150, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    postal_code = models.CharField(max_length=10, verbose_name='postal code', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'address'
        verbose_name_plural = 'addresses'

    def __str__(self):
        return f"{self.address}, {self.landmark if self.landmark else ''}, {self.city if self.city else ''}, {self.state if self.state else ''}, {self.country if self.country else ''} - {self.pincode if self.pincode else self.postal_code if self.postal_code else ''}"


class UserModel(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    role = models.ForeignKey(RoleModel,on_delete=models.CASCADE,null=True,blank=True)
    mobile_no =models.CharField(max_length=15,null=True,blank=True)
    address = models.ManyToManyField(AddressModel, blank=True)
    firm_name = models.CharField(max_length=100,blank=True,null=True)
    token = models.CharField(max_length=255,blank=True,null=True)
    approved_status = models.CharField(max_length=100,null=True,blank=True,choices=[('Pending','Pending'),('Approved','Approved')])
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.email} - {self.role.type if self.role else self.email}'
    
    def usergroups(self):
        return "".join([l.name for l in self.groups.all()])

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class DeviceModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    imei_number = models.CharField(max_length=255,null=True,blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.imei_number


class ClassModel(models.Model):
    """Represents a class/section like 8A, 9B, etc."""
    standard = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Class standard (1-12)"
    )
    section = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        help_text="Section name like A, B, C (optional)"
    )
    academic_year = models.CharField(
        max_length=20, 
        default='2024-25',
        help_text="Academic year like 2024-25"
    )
    
    # NO ManyToManyField here!
    # Students are linked via ForeignKey in StudentModel
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        unique_together = ['standard', 'section', 'academic_year']
    
    def __str__(self):
        section_str = f"{self.section}" if self.section else ""
        return f"Class {self.standard}{section_str} ({self.academic_year})"

    # Helper method to get student count
    def student_count(self):
        return self.students.count()

    # Helper method for API display
    def get_display_name(self):
        """Returns simple class display without academic year (e.g., 'Class 8A')"""
        section_str = f"{self.section}" if self.section else ""
        return f"Class {self.standard}{section_str}"

    # Helper method for API serialization
    def to_dict(self):
        """Returns dict representation for APIs"""
        return {
            'id': self.id,
            'standard': self.standard,
            'section': self.section or '',
            'academic_year': self.academic_year,
            'display_name': self.get_display_name(),
            'student_count': self.student_count()
        } 


class StudentModel(models.Model):
    device_id = models.ForeignKey(DeviceModel,on_delete=models.DO_NOTHING,null=True,blank=True)
    parent = models.ManyToManyField(UserModel,blank=True) # stores all customers, parents and teachers
    student_name = models.CharField(max_length=255)
    email = models.EmailField(null=True,blank=True)
    student_class = models.ForeignKey(ClassModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def __str__(self):
        return self.student_name
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

class EmployeeModel(models.Model):
    user = models.ForeignKey(UserModel,on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=255)
    email = models.EmailField(null=True,blank=True)
    department = models.CharField(max_length=255,null=True,blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.employee_id})"



class VendorModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    contact_email = models.EmailField(null=True,blank=True)
    contact_phone = PhoneNumberField(null=True,blank=True)

class InventoryModel(models.Model):
    vendor = models.ForeignKey(VendorModel, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    imei_number = models.CharField(max_length=255,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    


class TabletLeadModel(models.Model):

    LEAD_STAGE = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Demo Scheduled', 'Demo Scheduled'),
        ('Demo Done', 'Demo Done'),
        ('Negotiation', 'Negotiation'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Delivered', 'Delivered'),
        ('Lost', 'Lost'),
    ]

    CUSTOMER_TYPE = [
        ('Student', 'Student'),
        ('School', 'School'),
        ('College', 'College'),
        ('Institute', 'Institute'),
        ('Individual', 'Individual'),
    ]

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Paid', 'Paid'),
    ]

    name = models.CharField(max_length=255)
    mobile = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(blank=True, null=True)

    customer_type = models.CharField(max_length=30, choices=CUSTOMER_TYPE)
    school_name = models.CharField(max_length=255, blank=True, null=True)

    tablet_model = models.CharField(max_length=100)
    tablet_variant = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    price_per_unit = models.FloatField(null=True, blank=True)
    total_price = models.FloatField(null=True, blank=True)

    demo_required = models.BooleanField(default=False)
    demo_done = models.BooleanField(default=False)
    demo_date = models.DateField(blank=True, null=True)

    stage = models.CharField(max_length=50, choices=LEAD_STAGE, default='New')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')

    delivery_date = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL, null=True, related_name="tablet_leads_created"
    )
    assigned_to = models.ForeignKey(
        EmployeeModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="tablet_leads_assigned"
    )
    comment = models.TextField(blank=True, null=True)


    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.tablet_model}"



class TabletLeadFollowUpModel(models.Model):

    FOLLOWUP_TYPE = [
        ('Call', 'Call'),
        ('Whatsapp', 'WhatsApp'),
        ('Demo', 'Demo'),
        ('Meeting', 'Meeting'),
        ('Payment', 'Payment Follow-Up'),
        ('Delivery', 'Delivery Follow-Up'),
        ('Support', 'Support'),
    ]

    LEAD_STAGE = [
        ('Contacted', 'Contacted'),
        ('Demo Scheduled', 'Demo Scheduled'),
        ('Demo Done', 'Demo Done'),
        ('Negotiation', 'Negotiation'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Delivered', 'Delivered'),
        ('Lost', 'Lost'),
    ]

    tablet_lead = models.ForeignKey(
        TabletLeadModel,
        on_delete=models.CASCADE,
        related_name='followups'
    )

    followup_type = models.CharField(
        max_length=30,
        choices=FOLLOWUP_TYPE
    )

    followup_date = models.DateTimeField(
        help_text="Next follow-up date & time"
    )

    comment = models.TextField()

    followup_by = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tablet_followups'
    )

    stage_update = models.CharField(
        max_length=50,
        choices=LEAD_STAGE,
        blank=True,
        null=True,
        help_text="Update lead stage after this follow-up"
    )

    next_followup_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="If another follow-up is required"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tablet Lead Follow-Up"
        verbose_name_plural = "Tablet Lead Follow-Ups"

    def __str__(self):
        return f"{self.tablet_lead.name} - {self.followup_type}"


    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)

    #     if self.stage_update:
    #         self.tablet_lead.stage = self.stage_update
    #         self.tablet_lead.save(update_fields=['stage'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.stage_update:
            self.tablet_lead.stage = self.stage_update

        if self.comment:
            self.tablet_lead.comment = self.comment

        self.tablet_lead.save(update_fields=['stage', 'comment'])


# ============================================================================
# NEW MODELS FOR PHASE 2 - Parents & Teachers Mobile Apps
# ============================================================================


class TeacherAssignmentModel(models.Model):
    """
    Assigns teachers to specific classes and subjects.
    Solves: Math teacher → Class 8A, 8B → Math subject only
    """
    TEACHER_ROLE_CHOICES = [
        ('subject_teacher', 'Subject Teacher'),  # Teaches only assigned subjects
        ('class_teacher', 'Class Teacher'),      # Homeroom teacher, sees all subjects for their class
        ('principal', 'Principal/Admin'),        # Full school access
    ]
    
    teacher = models.ForeignKey(
        UserModel, 
        on_delete=models.CASCADE, 
        related_name='teacher_assignments',
        limit_choices_to={'role__type': 'Teacher'}
    )
    
    assigned_classes = models.ManyToManyField(
        ClassModel, 
        related_name='assigned_teachers',
        help_text="Classes this teacher teaches (e.g., 8A, 8B, 9A)"
    )
    
    assigned_subjects = models.ManyToManyField(
        'tablet_app.Subject', 
        related_name='assigned_teachers',
        help_text="Subjects this teacher can teach (e.g., Math, Science)"
    )
    
    teacher_role = models.CharField(
        max_length=20, 
        choices=TEACHER_ROLE_CHOICES, 
        default='subject_teacher'
    )
    
    # For class teachers - which class are they the homeroom teacher for
    homeroom_class = models.ForeignKey(
        ClassModel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='homeroom_teacher',
        help_text="If class teacher, which class is their homeroom"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Teacher Assignment"
        verbose_name_plural = "Teacher Assignments"
        unique_together = ['teacher']  # One assignment record per teacher
    
    def __str__(self):
        subjects = ", ".join([s.name for s in self.assigned_subjects.all()[:3]])
        classes = ", ".join([str(c) for c in self.assigned_classes.all()[:3]])
        return f"{self.teacher.first_name} - {subjects} → {classes}"


class StudentGoalModel(models.Model):
    """Goal setting system for parents/teachers to track student progress"""
    GOAL_TYPES = [
        ('score', 'Score Target'),
        ('consistency', 'Consistency'),
        ('study_time', 'Study Time'),
        ('improvement', 'Improvement'),
    ]
    
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(choices=GOAL_TYPES, max_length=20)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    subject = models.ForeignKey('tablet_app.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, related_name='created_goals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_achieved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.student_name} - {self.goal_type}: {self.target_value}"

    class Meta:
        verbose_name = "Student Goal"
        verbose_name_plural = "Student Goals"


class BatchModel(models.Model):
    """Batch/Section management for tuitions (Morning/Evening batches)"""
    name = models.CharField(max_length=100)  # "Morning", "Evening", "Weekend"
    teacher = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='batches')
    students = models.ManyToManyField(StudentModel, blank=True, related_name='batches')
    timing = models.CharField(max_length=50, null=True, blank=True)  # "6:00 AM - 8:00 AM"
    days = models.JSONField(default=list)  # ["Mon", "Wed", "Fri"]
    class_ref = models.ForeignKey(
        'ClassModel',  
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='batches',
        help_text="Which class this batch belongs to"
    )
    student_class = models.IntegerField(null=True, blank=True)
    subject = models.ForeignKey('tablet_app.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.teacher.first_name} ({self.students.count()} students)"

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"


class HomeworkModel(models.Model):
    """Homework assignments (separate from tests)"""
    title = models.CharField(max_length=255)
    subject = models.ForeignKey('tablet_app.Subject', on_delete=models.SET_NULL, null=True)
    description = models.TextField(null=True, blank=True)
    due_date = models.DateTimeField()
    assigned_to = models.ManyToManyField(StudentModel, blank=True, related_name='assigned_homework')
    batch = models.ForeignKey(BatchModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='homework')
    total_marks = models.IntegerField(default=100)
    created_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, related_name='created_homework')
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(
        'tablet_app.StudentGroupModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_homework'
    )

    def __str__(self):
        return f"{self.title} - {self.subject.name if self.subject else 'No Subject'}"

    class Meta:
        verbose_name = "Homework"
        verbose_name_plural = "Homework"


class HomeworkSubmissionModel(models.Model):
    """Track homework submissions from students"""
    homework = models.ForeignKey(HomeworkModel, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='homework_submissions')
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.IntegerField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.student_name} - {self.homework.title}"

    class Meta:
        verbose_name = "Homework Submission"
        verbose_name_plural = "Homework Submissions"
        unique_together = ['homework', 'student']


class TeacherRemarkModel(models.Model):
    """Teacher remarks on students visible to parents"""
    REMARK_TYPES = [
        ('general', 'General'),
        ('concern', 'Concern'),
        ('appreciation', 'Appreciation'),
    ]
    
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='teacher_remarks')
    teacher = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, related_name='given_remarks')
    remark = models.TextField()
    remark_type = models.CharField(choices=REMARK_TYPES, max_length=20, default='general')
    is_visible_to_parent = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher.first_name if self.teacher else 'Unknown'} → {self.student.student_name}: {self.remark_type}"

    class Meta:
        verbose_name = "Teacher Remark"
        verbose_name_plural = "Teacher Remarks"
        ordering = ['-created_at']


class AchievementModel(models.Model):
    """Achievement/Badge definitions"""
    CRITERIA_TYPES = [
        ('consistency', 'Consistency Days'),
        ('test_count', 'Tests Completed'),
        ('improvement', 'Score Improvement'),
        ('study_time', 'Study Hours'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_icon = models.CharField(max_length=50)  # emoji or icon name like "🏆", "⭐", "🔥"
    criteria_type = models.CharField(choices=CRITERIA_TYPES, max_length=50)
    criteria_value = models.IntegerField()  # e.g., 5 days for consistency

    def __str__(self):
        return f"{self.badge_icon} {self.name}"

    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"


class StudentAchievementModel(models.Model):
    """Track achievements earned by students"""
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(AchievementModel, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.student_name} earned {self.achievement.name}"

    class Meta:
        verbose_name = "Student Achievement"
        verbose_name_plural = "Student Achievements"
        unique_together = ['student', 'achievement']


class BadgeModel(models.Model):
    """
    Master list of all available badges in the system
    """
    BADGE_TYPE_CHOICES = (
        ('performance', 'Performance'),      # Score based
        ('consistency', 'Consistency'),      # Study streak based
        ('improvement', 'Improvement'),      # Score improvement
        ('completion', 'Completion'),        # Test completion
        ('speed', 'Speed'),                  # Fast completion
        ('subject', 'Subject'),              # Subject specific
    )

    name        = models.CharField(max_length=255)
    description = models.TextField()
    badge_type  = models.CharField(max_length=50, choices=BADGE_TYPE_CHOICES)
    icon        = models.CharField(max_length=100, null=True, blank=True)  # icon name or emoji
    threshold   = models.FloatField(help_text='Value needed to earn this badge (score%, streak days, etc)')
    subject     = models.ForeignKey(
        'tablet_app.Subject',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text='If subject-specific badge'
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentBadgeModel(models.Model):
    """
    Badges earned by students
    """
    student    = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='badges')
    badge      = models.ForeignKey(BadgeModel, on_delete=models.CASCADE, related_name='earned_by')
    earned_at  = models.DateTimeField(auto_now_add=True)
    context    = models.JSONField(null=True, blank=True, help_text='Extra info like test_id, score, streak_count')

    class Meta:
        unique_together = ('student', 'badge')  # Each badge earned once

    def __str__(self):
        return f"{self.student} - {self.badge.name}"


# ============================================================
# 2. LEARNING STYLE DETECTION
# ============================================================

class LearningStyleModel(models.Model):
    """
    Stores detected learning style for each student.
    Detected automatically from study behavior.

    Visual   → studies PDF/images more, high interaction_count
    Reading  → long study sessions, high page count
    Practice → attempts many tests, short sessions
    Mixed    → balanced across all
    """
    STYLE_CHOICES = (
        ('visual',    'Visual Learner'),
        ('reading',   'Reading Learner'),
        ('practice',  'Practice Learner'),
        ('mixed',     'Mixed Learner'),
    )

    student           = models.OneToOneField(StudentModel, on_delete=models.CASCADE, related_name='learning_style')
    style             = models.CharField(max_length=50, choices=STYLE_CHOICES, default='mixed')
    visual_score      = models.FloatField(default=0)   # interaction_count avg
    reading_score     = models.FloatField(default=0)   # avg session duration
    practice_score    = models.FloatField(default=0)   # test attempts count
    confidence        = models.FloatField(default=0)   # 0-100, how confident the detection is
    last_calculated   = models.DateTimeField(auto_now=True)
    data_points       = models.IntegerField(default=0) # how many sessions used for detection

    def __str__(self):
        return f"{self.student} - {self.style}"


# ============================================================
# 3. REWARD SUGGESTION SYSTEM
# ============================================================

class RewardModel(models.Model):
    """
    Master list of rewards teachers/parents can give students
    """
    REWARD_TYPE_CHOICES = (
        ('digital',   'Digital Reward'),    # e.g. sticker, certificate
        ('activity',  'Activity Reward'),   # e.g. extra break, game time
        ('privilege', 'Privilege Reward'),  # e.g. class monitor, helper
        ('praise',    'Praise Reward'),     # e.g. star of the week
    )

    name        = models.CharField(max_length=255)
    description = models.TextField()
    reward_type = models.CharField(max_length=50, choices=REWARD_TYPE_CHOICES)
    icon        = models.CharField(max_length=100, null=True, blank=True)
    min_score   = models.FloatField(default=0,   help_text='Min avg score% to suggest this reward')
    max_score   = models.FloatField(default=100, help_text='Max avg score% to suggest this reward')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentRewardModel(models.Model):
    """
    Rewards assigned to students by teacher or parent
    """
    student     = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='rewards')
    reward      = models.ForeignKey(RewardModel, on_delete=models.CASCADE, related_name='given_to')
    given_by    = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, related_name='given_rewards')
    note        = models.TextField(null=True, blank=True)
    given_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.reward.name}"


class NotificationPreferenceModel(models.Model):
    """
    Stores notification preferences linked to both StudentModel and UserModel.
    Either student or user must be set (not both required).
    """

    student = models.OneToOneField(
        StudentModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notification_preferences'
    )
    user = models.OneToOneField(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notification_preferences'
    )
 
    homework_assigned   = models.BooleanField(default=True)
    homework_due        = models.BooleanField(default=True)
    homework_graded     = models.BooleanField(default=True)
 
    test_scheduled      = models.BooleanField(default=True)
    test_result         = models.BooleanField(default=True)
 
    goal_achieved       = models.BooleanField(default=True)
    badge_earned        = models.BooleanField(default=True)
    weekly_report       = models.BooleanField(default=True)
 
    teacher_remark      = models.BooleanField(default=True)
 
    push_enabled        = models.BooleanField(default=True)
    email_enabled       = models.BooleanField(default=False)
    sms_enabled         = models.BooleanField(default=False)
 
    updated_at          = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
 
    def __str__(self):
        owner = self.student or self.user
        return f"Preferences - {owner}"
 
 
