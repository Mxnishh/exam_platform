from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Exam,Question
from .models import Option
from .models import Submission
from .models import Answer
from .models import ActivityLog
from django.utils.timezone import localtime
from .models import Department

class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('submission', 'event_type', 'formatted_timestamp')

    def formatted_timestamp(self, obj):
        return localtime(obj.timestamp)


admin.site.register(User, CustomUserAdmin)
admin.site.register(Question)
admin.site.register(Exam)
admin.site.register(Option)
admin.site.register(Submission)
admin.site.register(Answer)
admin.site.register(Department)