from django.db import models


class pdfGroupModel(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class pdfLibraryModel(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    pdf_file = models.FileField(upload_to='files', null=True, blank=True)
    total_pages = models.IntegerField()
    group = models.ManyToManyField(pdfGroupModel,blank=True)
    is_custom = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    student = models.ForeignKey('user_management.StudentModel', on_delete=models.CASCADE,blank=True,null=True, related_name='library')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title



class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class TestModel(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING, null=True, blank=True)
    pdf = models.ManyToManyField(pdfLibraryModel, related_name='test')
    number_of_questions = models.IntegerField()
    question_type = models.CharField(
        choices=(
            ('MCQ', 'MCQ'),
            ('Short Answer', 'Short Answer'),
            ('True/False', 'True/False'),
            ('Mixed', 'Mixed')
        ),
        max_length=255,
        default='MCQ'
    )
    duration_minutes = models.IntegerField(null=True, blank=True)
    total_marks = models.IntegerField()
    shuffle_questions = models.BooleanField(default=False)
    enable_timer = models.BooleanField(default=False)
    student = models.ManyToManyField('user_management.StudentModel', related_name='tests', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('user_management.UserModel', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


class QuestionsModel(models.Model):
    test = models.ForeignKey(TestModel, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=255, null=True, blank=True)
    marks = models.IntegerField()

    def __str__(self):
        return self.question_text


class QuestionOptionsModel(models.Model):
    question = models.ForeignKey(QuestionsModel, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text
    

class StudentTestAttemptModel(models.Model):
    student = models.ForeignKey('user_management.StudentModel', on_delete=models.CASCADE, related_name='student')
    test = models.ForeignKey(TestModel, on_delete=models.CASCADE, related_name='testattempt')
    score = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completes = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.test}"
    

class StudentAnswerModel(models.Model):
    attempt = models.ForeignKey(StudentTestAttemptModel, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuestionsModel, on_delete=models.CASCADE, related_name='question')
    selected_option = models.ForeignKey(QuestionOptionsModel, on_delete=models.CASCADE, related_name='selected_option')

    def __str__(self):
        return f"{self.attempt} - {self.question}"

class Chapter(models.Model):
    name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    
class StudySession(models.Model):
    student = models.ForeignKey('user_management.StudentModel', on_delete=models.CASCADE)

    subject = models.ForeignKey(
        Subject,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    duration = models.IntegerField(null=True, blank=True)  # in minutes

    interaction_count = models.IntegerField(default=0)
    # clicks / scroll / activity signals

    is_active = models.BooleanField(default=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    pdfs_opened = models.ManyToManyField(pdfLibraryModel, blank=True)
    offline_usage = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.duration = int((self.end_time - self.start_time).total_seconds() / 60)
        super().save(*args, **kwargs)


class StudentGroupModel(models.Model):
    name = models.CharField(max_length=255)
    students = models.ManyToManyField('user_management.StudentModel', related_name='groups')
    
    created_by = models.ForeignKey(
        'user_management.UserModel', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_student_groups',
        limit_choices_to={'role__type': 'Teacher'}
    )
    subject = models.ForeignKey(
        'tablet_app.Subject', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="If subject-specific group like 'Weak in Algebra'"
    )
    class_ref = models.ForeignKey(
        'user_management.ClassModel', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_groups'
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.students.count()} students)"
    
class ReportModel(models.Model):
   
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}"

