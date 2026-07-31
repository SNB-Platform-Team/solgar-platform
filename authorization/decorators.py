"""
authorization app — view decorators for screen-based access control.

Use @require_screen("CODE") on a view to ensure the current user's access
level includes that screen. Superusers bypass the check. Unauthorized users
are redirected to the dashboard with a message.
"""

from functools import wraps
from typing import Any, Callable

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def require_screen(screen_code: str) -> Callable:
    """
    Restrict a view to users whose access level includes `screen_code`.

    Args:
        screen_code: The screen code required to access the view.

    Returns:
        A view decorator.
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            user = request.user

            # Not logged in → send to login.
            if not user.is_authenticated:
                return redirect("accounts:login")

            # Superusers may access everything.
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            level = getattr(user, "access_level", None)
            if level is not None and screen_code in level.screen_codes():
                return view_func(request, *args, **kwargs)

            # Authenticated but not authorized for this screen.
            messages.error(request, "У вас нет доступа к этому разделу.")
            return redirect("accounts:home")

        return wrapper

    return decorator