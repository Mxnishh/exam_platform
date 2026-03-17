"""
WSGI config for exam_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_system.settings')

application = get_wsgi_application()

User = get_user_model()

try:
    user, created = User.objects.get_or_create(username="admin")
    user.set_password("admin123")
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print("✅ Admin ensured")
except Exception as e:
    print("Admin creation error:", e)
