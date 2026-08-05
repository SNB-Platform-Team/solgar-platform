"""
approvals app — business logic layer.

Handles request creation (with automatic approver routing) and approval
decisions. Views call services; services call the repository.
"""

from django.utils import timezone

from .models import EquipmentRequest
from .repositories import EquipmentRequestRepository


class ApprovalError(Exception):
    """Raised when a request action is not allowed."""


class EquipmentRequestService:
    """Business operations for the equipment request workflow."""

    def __init__(self) -> None:
        """Wire up the repository dependency."""
        self.repository = EquipmentRequestRepository()

    def submit_request(self, requester, item: str, reason: str) -> EquipmentRequest:
        """
        Create a request and route it to the requester's manager.

        Args:
            requester: The user submitting the request.
            item: The equipment being requested.
            reason: Optional justification.

        Returns:
            The created EquipmentRequest.

        Raises:
            ApprovalError: If the requester has no manager to route to.
        """
        approver = getattr(requester, "manager", None)
        if approver is None:
            raise ApprovalError(
                "Не задан руководитель для маршрутизации заявки."
            )
        return self.repository.create(requester, approver, item.strip(), reason.strip())

    def approve(self, request_obj: EquipmentRequest, approver, comment: str = "") -> None:
        """
        Approve a pending request.

        Args:
            request_obj: The request to approve.
            approver: The user making the decision.
            comment: Optional decision comment.

        Raises:
            ApprovalError: If the user is not the assigned approver, or the
                request is not pending.
        """
        self._guard_decision(request_obj, approver)
        request_obj.status = EquipmentRequest.Status.APPROVED
        request_obj.decision_comment = comment.strip()
        request_obj.decided_at = timezone.now()
        request_obj.save(update_fields=["status", "decision_comment", "decided_at"])

    def reject(self, request_obj: EquipmentRequest, approver, comment: str = "") -> None:
        """
        Reject a pending request.

        Raises:
            ApprovalError: If the user is not the assigned approver, or the
                request is not pending.
        """
        self._guard_decision(request_obj, approver)
        request_obj.status = EquipmentRequest.Status.REJECTED
        request_obj.decision_comment = comment.strip()
        request_obj.decided_at = timezone.now()
        request_obj.save(update_fields=["status", "decision_comment", "decided_at"])

    def cancel(self, request_obj: EquipmentRequest, requester) -> None:
        """
        Cancel a pending request. Only the original requester may cancel,
        and only while the request is still pending.

        Raises:
            ApprovalError: If the user is not the requester, or the request
                is not pending.
        """
        if request_obj.requester_id != requester.id:
            raise ApprovalError("Вы можете отменить только свои заявки.")
        if not request_obj.is_pending:
            raise ApprovalError("Заявка уже обработана и не может быть отменена.")

        request_obj.status = EquipmentRequest.Status.CANCELLED
        request_obj.decided_at = timezone.now()
        request_obj.save(update_fields=["status", "decided_at"])

    def _guard_decision(self, request_obj: EquipmentRequest, approver) -> None:
        """Ensure the user may decide on this request."""
        if request_obj.approver_id != approver.id:
            raise ApprovalError("Вы не назначены ответственным за эту заявку.")
        if not request_obj.is_pending:
            raise ApprovalError("Заявка уже обработана.")