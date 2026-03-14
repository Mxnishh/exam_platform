import random
from urllib import request
import csv
from django.http import HttpResponse
from django.shortcuts import render
from .models import Exam
from django.shortcuts import get_object_or_404, redirect
from .models import Exam, Submission
from django.utils import timezone
from .models import Answer, Option
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import ActivityLog
from django.db.models import Avg, Max, Min, Count
from .decorators import instructor_required
from django.shortcuts import redirect, render, get_object_or_404
from .forms import ExamForm
from .models import Exam, Question, Option

@login_required
def exam_list(request):

    exams = Exam.objects.all()
    exam_data = []

    for exam in exams:
        submission = Submission.objects.filter(
            student=request.user,
            exam=exam
        ).first()

        exam_data.append({
            "exam": exam,
            "submission": submission
        })

    return render(request, "core/exam_list.html", {
        "exam_data": exam_data
    })


@login_required
def start_exam(request, exam_id):

    if request.user.role != "STUDENT":
        return redirect('exam_list')

    exam = get_object_or_404(Exam, id=exam_id)

    # Check if ANY submission exists (submitted or not)
    existing_submission = Submission.objects.filter(
        student=request.user,
        exam=exam
    ).order_by('-start_time').first()

    if existing_submission:
        # If already submitted → show result
        if existing_submission.is_submitted:
            return redirect('exam_result', existing_submission.id)
        # If not submitted → continue unfinished attempt
        else:
            return redirect('exam_detail', existing_submission.id)

    # If no submission exists → create one
    submission = Submission.objects.create(
        student=request.user,
        exam=exam
    )

    ActivityLog.objects.create(
    submission=submission,
    event_type='STARTED'
    )

    return redirect('exam_detail', submission.id)

@login_required
def exam_detail(request, submission_id):

    if request.user.role != "STUDENT":
        return redirect('exam_list')

    submission = get_object_or_404(Submission, id=submission_id)

    # Randomize questions
    questions = list(submission.exam.questions.all())
    random.shuffle(questions)

    # Randomize options for each question
    for question in questions:
        options = list(question.options.all())
        random.shuffle(options)
        question.shuffled_options = options

    # Calculate remaining time
    end_time = submission.start_time + timedelta(minutes=submission.exam.duration_minutes)
    remaining_seconds = int((end_time - timezone.now()).total_seconds())

    if remaining_seconds <= 0:
        submission.calculate_score()
        submission.end_time = timezone.now()
        submission.save()

        ActivityLog.objects.create(
            submission=submission,
            event_type='AUTO_SUBMIT_TIME'
        )

        return redirect('exam_result', submission.id)

    if request.method == "POST":

        for question in questions:

            selected_option_id = request.POST.get(f"question_{question.id}")

            if selected_option_id:

                selected_option = Option.objects.get(id=selected_option_id)

                Answer.objects.create(
                    submission=submission,
                    question=question,
                    selected_option=selected_option
                )

        submission.calculate_score()

        submission.end_time = timezone.now()
        submission.save()

        ActivityLog.objects.create(
            submission=submission,
            event_type='SUBMITTED'
        )

        return redirect('exam_result', submission.id)

    return render(request, 'core/exam_detail.html', {
        'submission': submission,
        'questions': questions,
        'remaining_seconds': remaining_seconds
    })

@login_required
def exam_result(request, submission_id):

    submission = get_object_or_404(Submission, id=submission_id)

    # If the user is a student, they can only see their own result
    if request.user.role == "STUDENT":
        if submission.student != request.user:
            return redirect('exam_list')

    # If the user is an instructor, they can only see results of their exams
    elif request.user.role == "INSTRUCTOR":
        if submission.exam.instructor != request.user:
            return redirect('instructor_dashboard')

    questions = submission.exam.questions.all()

    total_marks = sum(q.marks for q in questions)
    score = submission.total_score

    percentage = 0
    if total_marks > 0:
        percentage = round((score / total_marks) * 100, 2)

        return render(request, 'core/exam_result.html', {
        'submission': submission,
        'total_marks': total_marks,
        'percentage': percentage
        })

@login_required
@instructor_required
def instructor_dashboard(request):

    print("USER:", request.user.username)
    print("ROLE:", request.user.role)
    print("AUTH:", request.user.is_authenticated)

    exams = Exam.objects.filter(instructor=request.user)

    exam_data = []

    for exam in exams:
        submissions = Submission.objects.filter(exam=exam)

        has_submissions = submissions.exists()

        status = "Draft"
        if has_submissions:
            status = "Attempted"

        stats = submissions.aggregate(
            total_attempts=Count("id"),
            avg_score=Avg("total_score"),
            highest_score=Max("total_score"),
            lowest_score=Min("total_score"),
        )

        # NEW: collect score list
        scores = list(submissions.values_list("total_score", flat=True))

        exam_data.append({
            "exam": exam,
            "stats": stats,
            "has_submissions": has_submissions,
            "status": status,
            "scores": scores
        })

    return render(request, "core/instructor_dashboard.html", {
        "exam_data": exam_data
    })


from django.shortcuts import redirect

def home_redirect(request):

    if not request.user.is_authenticated:
        return redirect("login")

    # Django superuser (admin panel)
    if request.user.is_superuser:
        return redirect("/admin/")

    role = request.user.role.upper()

    if role == "STUDENT":
        return redirect("student_dashboard")

    elif role == "INSTRUCTOR":
        return redirect("instructor_dashboard")

    return redirect("exam_list")

def landing_page(request):
    return render(request, "core/landing.html")

@login_required
@instructor_required
def create_exam(request):

    if request.method == "POST":
        form = ExamForm(request.POST)

        if form.is_valid():
            exam = form.save(commit=False)
            exam.instructor = request.user
            exam.save()

            return redirect("instructor_dashboard")

    else:
        form = ExamForm()

    return render(request, "core/create_exam.html", {"form": form})

@login_required
@instructor_required
def add_question(request, exam_id):

    exam = Exam.objects.get(id=exam_id)

    # 🔒 Prevent adding questions if students already attempted the exam
    submissions = Submission.objects.filter(exam=exam)

    if submissions.exists():
        return redirect("instructor_dashboard")

    if request.method == "POST":
        question_text = request.POST.get("question")

        option1 = request.POST.get("option1")
        option2 = request.POST.get("option2")
        option3 = request.POST.get("option3")
        option4 = request.POST.get("option4")

        correct_option = request.POST.get("correct_option")

        # Create question
        question = Question.objects.create(
            exam=exam,
            text=question_text
        )

        # Create options
        Option.objects.create(question=question, text=option1, is_correct=(correct_option=="1"))
        Option.objects.create(question=question, text=option2, is_correct=(correct_option=="2"))
        Option.objects.create(question=question, text=option3, is_correct=(correct_option=="3"))
        Option.objects.create(question=question, text=option4, is_correct=(correct_option=="4"))

        # ✅ Update exam status after first question is added
        if exam.questions.exists():
            exam.status = "Published"
            exam.save()

        return redirect("add_question", exam_id=exam.id)

    questions = Question.objects.filter(exam=exam)

    return render(request, "core/add_question.html", {
        "exam": exam,
        "questions": questions
    })

@login_required
@instructor_required
def exam_submissions(request, exam_id):

    exam = Exam.objects.get(id=exam_id)

    submissions = Submission.objects.filter(exam=exam)

    return render(request, "core/exam_submissions.html", {
        "exam": exam,
        "submissions": submissions
    })

@login_required
@instructor_required
def reset_attempt(request, submission_id):

    submission = get_object_or_404(Submission, id=submission_id)

    # Ensure instructor owns the exam
    if submission.exam.instructor != request.user:
        return redirect("instructor_dashboard")

    submission.delete()

    return redirect("exam_submissions", exam_id=submission.exam.id)

@login_required
@instructor_required
def delete_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    # Ensure instructor owns this exam
    if exam.instructor != request.user:
        return redirect("instructor_dashboard")

    exam.delete()

    return redirect("instructor_dashboard")

@login_required
@instructor_required
def edit_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    # Ensure instructor owns this exam
    if exam.instructor != request.user:
        return redirect("instructor_dashboard")

    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect("instructor_dashboard")
    else:
        form = ExamForm(instance=exam)

    return render(request, "core/edit_exam.html", {
        "form": form,
        "exam": exam
    })

@login_required
@instructor_required
def edit_question(request, question_id):

    question = get_object_or_404(Question, id=question_id)

    if request.method == "POST":
        question.text = request.POST.get("question")
        question.save()

        return redirect("add_question", exam_id=question.exam.id)

    return render(request, "core/edit_question.html", {
        "question": question
    })

@login_required
@instructor_required
def delete_question(request, question_id):

    question = get_object_or_404(Question, id=question_id)

    exam_id = question.exam.id
    question.delete()

    return redirect("add_question", exam_id=exam_id)

@login_required
def my_results(request):

    if request.user.role != "STUDENT":
        return redirect("exam_list")

    submissions = Submission.objects.filter(student=request.user)

    return render(request, "core/my_results.html", {
        "submissions": submissions
    })

@login_required
def exam_instructions(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    return render(request, "core/exam_instructions.html", {
        "exam": exam
    })

@login_required
def student_dashboard(request):

    if request.user.role != "STUDENT":
        return redirect("exam_list")

    completed_exams = Submission.objects.filter(
        student=request.user,
        is_submitted=True
    ).count()

    total_exams = Exam.objects.count()

    available_exams = total_exams - completed_exams

    return render(request, "core/student_dashboard.html", {
        "available_exams": available_exams,
        "completed_exams": completed_exams,
        "total_exams": total_exams
    })

def export_results(request, exam_id):

    submissions = Submission.objects.filter(exam_id=exam_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="exam_results.csv"'

    writer = csv.writer(response)

    writer.writerow(["Student", "Score", "Submitted At"])

    for s in submissions:
        writer.writerow([
            s.student.username,
            s.total_score,
            s.submitted_at
        ])

    return response