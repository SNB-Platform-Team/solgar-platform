"""
approvals app — equipment request workflow.

An employee submits an equipment request; the system routes it to their
manager for approval. The request moves through a simple state machine:
PENDING → APPROVED or REJECTED. All decisions are recorded with a timestamp.
"""

from django.conf import settings
from django.db import models


class EquipmentRequest(models.Model):
    """A request by an employee for a piece of equipment, needing approval."""

    class Status(models.TextChoices):
        """Lifecycle states of a request."""

        PENDING = "PENDING", "На рассмотрении"
        APPROVED = "APPROVED", "Одобрено"
        REJECTED = "REJECTED", "Отклонено"

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="equipment_requests",
        verbose_name="Requester",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipment_approvals",
        verbose_name="Approver",
    )
    item = models.CharField("Equipment", max_length=200)
    reason = models.TextField("Reason", blank=True)
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    decision_comment = models.CharField("Decision comment", max_length=300, blank=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    decided_at = models.DateTimeField("Decided at", null=True, blank=True)

    class Meta:
        verbose_name = "Equipment request"
        verbose_name_plural = "Equipment requests"
        db_table = "approvals_equipment_request"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.item} — {self.requester} ({self.get_status_display()})"

    @property
    def is_pending(self) -> bool:
        """True if the request is still awaiting a decision."""
        return self.status == self.Status.PENDING