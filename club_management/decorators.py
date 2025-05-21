from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles, redirect_url='users:list_users'):
    """
    Decorator for views that checks whether the logged-in user has one of the required roles.
    It assumes that your User model (or its subclass) implements a get_role() method that returns
    the user's role as a string (e.g. "Club Leader", "Executive", "Activity Center Admin", "Club Member").
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect(redirect_url)
            user_role = request.user.get_role()
            if user_role not in roles:
                messages.error(request, "You do not have the required permissions to access this page.")
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
