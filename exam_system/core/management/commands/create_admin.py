from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model()

        user, created = User.objects.get_or_create(username="admin")

        user.set_password("admin123")  # 🔥 force reset password
        user.is_superuser = True
        user.is_staff = True
        user.save()

        if created:
            self.stdout.write("Superuser created")
        else:
            self.stdout.write("Superuser updated (password reset)")