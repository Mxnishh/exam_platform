from django.http import HttpResponseForbidden
from functools import wraps

def instructor_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = request.user

        if not user.is_authenticated:
            return HttpResponseForbidden("You must be logged in.")

        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        role = (user.role or "").upper()

        if role != "INSTRUCTOR":
            return HttpResponseForbidden("Only instructors can access this page.")

        return view_func(request, *args, **kwargs)

    return wrapper