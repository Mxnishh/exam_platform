from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('home/', views.home_redirect, name='home'),
    path('exams/', views.exam_list, name='exam_list'),
    path('start/<int:exam_id>/', views.start_exam, name='start_exam'),
    path('exam/<int:submission_id>/', views.exam_detail, name='exam_detail'),
    path('result/<int:submission_id>/', views.exam_result, name='exam_result'),
    path("instructor/dashboard/", views.instructor_dashboard, name="instructor_dashboard"),
    path('instructor/create-exam/', views.create_exam, name='create_exam'),
    path('instructor/exam/<int:exam_id>/add-question/', views.add_question, name='add_question'),
    path('instructor/exam/<int:exam_id>/submissions/',views.exam_submissions,name='exam_submissions'),
    path("instructor/submission/<int:submission_id>/reset/",views.reset_attempt,name="reset_attempt"),
    path("instructor/exam/<int:exam_id>/delete/",views.delete_exam,name="delete_exam"),
    path("instructor/exam/<int:exam_id>/edit/",views.edit_exam,name="edit_exam"),
    path("instructor/question/<int:question_id>/edit/",views.edit_question,name="edit_question"),
    path("instructor/question/<int:question_id>/delete/",views.delete_question,name="delete_question"),
    path("results/", views.my_results, name="my_results"),
    path("exam/<int:exam_id>/instructions/", views.exam_instructions, name="exam_instructions"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("export-results/<int:exam_id>/", views.export_results, name="export_results"),
]
