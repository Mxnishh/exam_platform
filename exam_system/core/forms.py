from django import forms
from .models import Exam
from .models import Question

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["title", "description", "duration_minutes"]

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control"}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']
