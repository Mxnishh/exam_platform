from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count
from django.contrib.auth.views import LoginView
from django.urls import reverse
from datetime import timedelta
import random
import csv

from .models import (
    Exam, Submission, Answer, Option,
    ActivityLog, Question, Subject
)
from .forms import ExamForm
from .decorators import instructor_required


# ===================== EXAM LIST =====================
@login_required
def exam_list(request):
    user = request.user
    now = timezone.now()

    if user.role.upper() == "STUDENT":
        exams = Exam.objects.filter(
            subject__department=user.department
        ).select_related("subject")

    elif user.role.upper() == "INSTRUCTOR":
        exams = Exam.objects.filter(
            instructor=user
        ).select_related("subject")

    else:
        exams = Exam.objects.all().select_related("subject")

    exam_data = []

    for exam in exams:
        submission = Submission.objects.filter(
            student=user,
            exam=exam
        ).first()

        if exam.start_time and exam.end_time:
            if now < exam.start_time:
                status = "upcoming"
            elif now > exam.end_time:
                status = "expired"
            else:
                status = "active"
        else:
            status = "active"

        exam_data.append({
            "exam": exam,
            "submission": submission,
            "status": status
        })

    return render(request, "core/exam_list.html", {"exam_data": exam_data})


# ===================== START EXAM =====================
@login_required
def start_exam(request, exam_id):

    if request.user.role.upper() != "STUDENT":
        return HttpResponseForbidden("Only students can start exams")

    exam = get_object_or_404(Exam, id=exam_id)
    now = timezone.now()

    if exam.start_time and exam.end_time:
        if not (exam.start_time <= now <= exam.end_time):
            return HttpResponseForbidden("Exam not active")

    existing_submission = Submission.objects.filter(
        student=request.user,
        exam=exam
    ).first()

    if existing_submission:
        if existing_submission.submitted_at:
            return redirect("exam_result", existing_submission.id)
        return redirect("exam_detail", existing_submission.id)

    submission = Submission.objects.create(
        student=request.user,
        exam=exam,
        start_time=now
    )

    ActivityLog.objects.create(
        submission=submission,
        event_type="STARTED"
    )

    return redirect("exam_detail", submission.id)


# ===================== EXAM DETAIL =====================
@login_required
def exam_detail(request, submission_id):

    if request.user.role.upper() != "STUDENT":
        return HttpResponseForbidden("Only students allowed")

    submission = get_object_or_404(Submission, id=submission_id)

    if submission.student != request.user:
        return HttpResponseForbidden("Not allowed")

    exam = submission.exam

    if submission.end_time:
        return HttpResponseForbidden("Exam already submitted")

    now = timezone.now()
    if not (exam.start_time <= now <= exam.end_time):
        return HttpResponseForbidden("Exam not active")

    questions = list(exam.questions.all())
    random.shuffle(questions)

    for q in questions:
        opts = list(q.options.all())
        random.shuffle(opts)
        q.shuffled_options = opts

    if submission.start_time:
        end_time = submission.start_time + timedelta(minutes=exam.duration_minutes)
        remaining_seconds = max(0, int((end_time - now).total_seconds()))
    else:
        remaining_seconds = exam.duration_minutes * 60

    if remaining_seconds <= 0:
        submission.calculate_score()
        submission.end_time = now
        submission.save()
        return redirect("exam_result", submission.id)

    if request.method == "POST":
        for q in questions:
            opt_id = request.POST.get(f"question_{q.id}")
            if opt_id:
                opt = get_object_or_404(Option, id=opt_id)

                Answer.objects.update_or_create(
                    submission=submission,
                    question=q,
                    defaults={"selected_option": opt}
                )

        submission.calculate_score()
        submission.end_time = now
        submission.save()

        return redirect("exam_result", submission.id)

    return render(request, "core/exam_detail.html", {
        "submission": submission,
        "questions": questions,
        "remaining_seconds": remaining_seconds
    })


# ===================== EXAM RESULT =====================
@login_required
def exam_result(request, submission_id):

    submission = get_object_or_404(Submission, id=submission_id)

    if request.user.role.upper() == "STUDENT":
        if submission.student != request.user:
            return HttpResponseForbidden("Not allowed")

    elif request.user.role.upper() == "INSTRUCTOR":
        if submission.exam.instructor != request.user:
            return HttpResponseForbidden("Not allowed")

    else:
        return HttpResponseForbidden("Access denied")

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


# ===================== INSTRUCTOR DASHBOARD =====================
@login_required
@instructor_required
def instructor_dashboard(request):

    exams = Exam.objects.filter(instructor=request.user)
    exam_data = []

    for exam in exams:
        submissions = Submission.objects.filter(exam=exam)

        stats = submissions.aggregate(
            total_attempts=Count("id"),
            avg_score=Avg("total_score"),
            highest_score=Max("total_score"),
            lowest_score=Min("total_score"),
        )

        scores = list(submissions.values_list("total_score", flat=True))

        exam_data.append({
            "exam": exam,
            "stats": stats,
            "scores": scores
        })

    return render(request, "core/instructor_dashboard.html", {
        "exam_data": exam_data
    })


# ===================== INSTRUCTOR SECURITY FIXES =====================

@login_required
@instructor_required
def exam_submissions(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    if exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    submissions = Submission.objects.filter(exam=exam)

    return render(request, "core/exam_submissions.html", {
        "exam": exam,
        "submissions": submissions
    })


@login_required
@instructor_required
def reset_attempt(request, submission_id):

    submission = get_object_or_404(Submission, id=submission_id)

    if submission.exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    submission.delete()

    return redirect("exam_submissions", exam_id=submission.exam.id)


@login_required
@instructor_required
def delete_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    if exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    exam.delete()

    return redirect("instructor_dashboard")


@login_required
@instructor_required
def edit_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    if exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect("instructor_dashboard")
    else:
        form = ExamForm(instance=exam)

    return render(request, "core/edit_exam.html", {"form": form})


@login_required
@instructor_required
def edit_question(request, question_id):

    question = get_object_or_404(Question, id=question_id)

    if question.exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        question.text = request.POST.get("question")
        question.save()
        return redirect("add_question", exam_id=question.exam.id)

    return render(request, "core/edit_question.html", {"question": question})


@login_required
@instructor_required
def delete_question(request, question_id):

    question = get_object_or_404(Question, id=question_id)

    if question.exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    exam_id = question.exam.id
    question.delete()

    return redirect("add_question", exam_id=exam_id)


# ===================== EXPORT (FIXED) =====================
@login_required
@instructor_required
def export_results(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    if exam.instructor != request.user:
        return HttpResponseForbidden("Not allowed")

    submissions = Submission.objects.filter(exam=exam)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="exam_results.csv"'

    writer = csv.writer(response)
    writer.writerow(["Student", "Score", "Submitted At"])

    for s in submissions:
        writer.writerow([s.student.username, s.total_score, s.end_time])

    return response