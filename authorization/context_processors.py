"""
authorization app — template context processors.

Exposes the set of screen codes the current user may access, so templates
(e.g. the sidebar) can show or hide navigation items by screen code.
"""

from typing import Any

from django.http import HttpRequest


def accessible_screens(request: HttpRequest) -> dict[str, Any]:
    """
    Add `accessible_screens` (a set of screen codes) to the template context.

    - Superusers implicitly see every screen.
    - Users with an access level see that level's active screens.
    - Everyone else sees nothing (empty set).
    """
    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return {"accessible_screens": set()}

    # Superusers bypass access-level checks entirely.
    if user.is_superuser:
        from .models import Screen

        codes = set(
            Screen.objects.filter(is_active=True).values_list("code", flat=True)
        )
        return {"accessible_screens": codes}

    level = getattr(user, "access_level", None)
    if level is None:
        return {"accessible_screens": set()}

    return {"accessible_screens": level.screen_codes()}