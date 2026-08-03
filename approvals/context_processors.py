"""
approvals app — template context processor.

Exposes the number of requests awaiting the current user's approval, so the
sidebar can show a pending-count badge on every page.
"""

from typing import Any

from django.http import HttpRequest

from .models import EquipmentRequest


def pending_approvals_count(request: HttpRequest) -> dict[str, Any]:
    """Add `pending_approvals_count` to the template context."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"pending_approvals_count": 0}

    count = EquipmentRequest.objects.filter(
        approver=user, status=EquipmentRequest.Status.PENDING
    ).count()
    return {"pending_approvals_count": count}