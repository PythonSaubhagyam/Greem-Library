from django.db import models
from user_management.models import *


class pdfGroupModel(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class pdfLibraryModel(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    pdf_file = models.FileField(upload_to='files', null=True, blank=True)
    total_pages = models.IntegerField()
    group = models.ManyToManyField(pdfGroupModel,blank=True)
    is_custom = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE,blank=True,null=True, related_name='library')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class TestModel(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
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
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='students')
    created_at = models.DateTimeField(auto_now_add=True)

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
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, related_name='student')
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
