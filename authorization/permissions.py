"""
authorization app — DRF permission classes for screen-based API access.

Mirrors the @require_screen view decorator, but for Django REST Framework
API views. Attach one screen code to an endpoint; a user may call it only
if their access level includes that screen (superusers bypass).

Usage (function-based DRF view):

    from authorization.permissions import HasScreen

    @api_view(["GET"])
    @permission_classes([HasScreen("PHARMACY")])
    def pharmacy_api(request):
        ...

Note: `permission_classes` expects classes, not instances. `HasScreen(code)`
returns a dynamically built subclass (a class), so it plugs in directly.
"""

from rest_framework.permissions import BasePermission


def _user_screen_codes(user) -> set:
    """Return the set of active screen codes this user can access.

    Superusers implicitly get everything. A user with an access level gets
    that level's active screens. Anyone else gets an empty set. Mirrors
    authorization.context_processors.accessible_screens."""
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser:
        from .models import Screen
        return set(
            Screen.objects.filter(is_active=True).values_list("code", flat=True)
        )
    level = getattr(user, "access_level", None)
    if level is None:
        return set()
    return level.screen_codes()


def HasScreen(screen_code: str):
    """Build a DRF permission class requiring `screen_code`.

    Returns a BasePermission subclass so it can be passed straight into
    @permission_classes([...])."""

    class _HasScreen(BasePermission):
        message = "У вас нет доступа к этому разделу."
        required_screen = screen_code

        def has_permission(self, request, view) -> bool:
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return False
            if user.is_superuser:
                return True
            return screen_code in _user_screen_codes(user)

    _HasScreen.__name__ = f"HasScreen_{screen_code}"
    return _HasScreen
