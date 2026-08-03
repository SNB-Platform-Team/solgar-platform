"""
approvals app — data access layer.

All database access for equipment requests. ORM only, no raw SQL.
"""

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import EquipmentRequest


class EquipmentRequestRepository:
    """Encapsulates database access for equipment requests."""

    def create(self, requester, approver, item: str, reason: str) -> EquipmentRequest:
        """Create a new pending request."""
        return EquipmentRequest.objects.create(
            requester=requester,
            approver=approver,
            item=item,
            reason=reason,
            status=EquipmentRequest.Status.PENDING,
        )

    def get_by_id(self, pk: int) -> EquipmentRequest:
        """Return a single request by ID, or 404."""
        return get_object_or_404(EquipmentRequest, pk=pk)

    def for_requester(self, user) -> QuerySet:
        """Return all requests created by a given user."""
        return EquipmentRequest.objects.filter(requester=user).select_related(
            "requester", "approver"
        )

    def pending_for_approver(self, user) -> QuerySet:
        """Return pending requests awaiting a given approver's decision."""
        return EquipmentRequest.objects.filter(
            approver=user, status=EquipmentRequest.Status.PENDING
        ).select_related("requester", "approver")

    def decided_by_approver(self, user) -> QuerySet:
        """Return requests this approver has already decided."""
        return EquipmentRequest.objects.filter(approver=user).exclude(
            status=EquipmentRequest.Status.PENDING
        ).select_related("requester", "approver")