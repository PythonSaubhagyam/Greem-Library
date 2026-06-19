from django.db import models

from django.conf import settings


# Homework assigned to students or classes
class HomeworkModel(models.Model):
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='homeworks_assigned')
	# assign to specific students (optional) or keep empty to assign to class/group
	# use a namespaced related_name to avoid conflicts with other apps
	students = models.ManyToManyField('user_management.StudentModel', blank=True, related_name='admin_homeworks')
	# simple class text field to indicate which class/section this homework targets
	target_class = models.CharField(max_length=128, blank=True, null=True)
	due_date = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.title} ({self.id})"


# Student submissions for homework
class HomeworkSubmissionModel(models.Model):
	homework = models.ForeignKey(HomeworkModel, on_delete=models.CASCADE, related_name='submissions')
	# use a unique related_name to avoid reverse accessor clashes with other apps
	student = models.ForeignKey('user_management.StudentModel', on_delete=models.CASCADE, related_name='admin_homework_submissions')
	submitted_at = models.DateTimeField(auto_now_add=True)
	content = models.TextField(blank=True, null=True)
	attachment = models.FileField(upload_to='homework_submissions/', blank=True, null=True)
	is_checked = models.BooleanField(default=False)
	checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_homeworks')
	marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

	def __str__(self):
		return f"Submission {self.id} - HW {self.homework_id} - Student {self.student_id}"


# Create your models here.
