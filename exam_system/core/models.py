from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('INSTRUCTOR', 'Instructor'),
        ('STUDENT', 'Student'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.role}"


class Exam(models.Model):

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'INSTRUCTOR'}
    )

    duration_minutes = models.IntegerField()

    # NEW FIELDS
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    DIFFICULTY_LEVELS = (
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    )

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    marks = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='MEDIUM')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text[:50]}"
    
class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options'
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text}"

class Submission(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'}
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    is_submitted = models.BooleanField(default=False)

    def calculate_score(self):
        score = 0
        for answer in self.answers.all():
            if answer.selected_option.is_correct:
                score += answer.question.marks

        self.total_score = score
        self.is_submitted = True
        self.submitted_at = timezone.now()
        self.save()


    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"
    
class Answer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.submission.student.username} - {self.question.text[:30]}"
    
class ActivityLog(models.Model):
    EVENT_CHOICES = (
        ('STARTED', 'Exam Started'),
        ('SUBMITTED', 'Exam Submitted'),
        ('AUTO_SUBMIT_TIME', 'Auto Submitted - Time Expired'),
        ('AUTO_SUBMIT_TAB', 'Auto Submitted - Tab Switch'),
    )

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )

    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.submission.student.username} - {self.event_type} - {self.timestamp}"