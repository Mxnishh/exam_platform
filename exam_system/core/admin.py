from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Exam, Question, Option, Submission, Answer, ActivityLog, Department, Subject
from django.utils.timezone import localtime


# ✅ USER ADMIN
class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'department')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role', 'department')}),
    )


# ✅ EXAM ADMIN (🔥 THIS FIXES YOUR ISSUE)
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'subject', 'duration_minutes')

    fields = (
        'title',
        'description',
        'instructor',
        'subject',   # ✅ NOW IT WILL SHOW
        'duration_minutes',
        'start_time',
        'end_time',
    )


# ✅ ACTIVITY LOG
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('submission', 'event_type', 'formatted_timestamp')

    def formatted_timestamp(self, obj):
        return localtime(obj.timestamp)


# ✅ REGISTER OTHERS
admin.site.register(User, CustomUserAdmin)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Submission)
admin.site.register(Answer)
admin.site.register(Department)
admin.site.register(Subject)