"""approvals app — views for the equipment request workflow."""

from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from authorization.decorators import require_screen

from .models import EquipmentRequest
from .repositories import EquipmentRequestRepository
from .services import ApprovalError, EquipmentRequestService


@login_required
@require_screen("REQUESTS")
def my_requests_view(request: HttpRequest) -> HttpResponse:
    """List the current user's own equipment requests."""
    requests = EquipmentRequestRepository().for_requester(request.user)
    return render(request, "approvals/my_requests.html", {"requests": requests})


@login_required
@require_screen("REQUESTS")
@require_http_methods(["GET", "POST"])
def create_request_view(request: HttpRequest) -> HttpResponse:
    """Submit a new equipment request, routed to the user's manager."""
    if request.method == "POST":
        item = request.POST.get("item", "").strip()
        reason = request.POST.get("reason", "").strip()

        if not item:
            messages.error(request, "Укажите оборудование.")
            return render(request, "approvals/create.html", {"item": item, "reason": reason})

        try:
            EquipmentRequestService().submit_request(request.user, item, reason)
        except ApprovalError as exc:
            messages.error(request, str(exc))
            return render(request, "approvals/create.html", {"item": item, "reason": reason})

        messages.success(request, "Заявка отправлена на рассмотрение.")
        return redirect("approvals:my_requests")

    return render(request, "approvals/create.html", {})


@login_required
@require_screen("APPROVALS")
def approval_inbox_view(request: HttpRequest) -> HttpResponse:
    """Show requests awaiting the current user's decision, plus decided ones."""
    repo = EquipmentRequestRepository()
    context: dict[str, Any] = {
        "pending": repo.pending_for_approver(request.user),
        "decided": repo.decided_by_approver(request.user)[:10],
    }
    return render(request, "approvals/inbox.html", context)


@login_required
@require_screen("APPROVALS")
@require_http_methods(["POST"])
def approve_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Approve a pending request."""
    repo = EquipmentRequestRepository()
    obj = repo.get_by_id(pk)
    comment = request.POST.get("comment", "").strip()

    try:
        EquipmentRequestService().approve(obj, request.user, comment)
        messages.success(request, "Заявка одобрена.")
    except ApprovalError as exc:
        messages.error(request, str(exc))

    return redirect("approvals:inbox")


@login_required
@require_screen("APPROVALS")
@require_http_methods(["POST"])
def reject_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Reject a pending request."""
    repo = EquipmentRequestRepository()
    obj = repo.get_by_id(pk)
    comment = request.POST.get("comment", "").strip()

    try:
        EquipmentRequestService().reject(obj, request.user, comment)
        messages.success(request, "Заявка отклонена.")
    except ApprovalError as exc:
        messages.error(request, str(exc))

    return redirect("approvals:inbox")


@login_required
@require_screen("REQUESTS")
@require_http_methods(["POST"])
def cancel_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Cancel the current user's own pending request."""
    repo = EquipmentRequestRepository()
    obj = repo.get_by_id(pk)

    try:
        EquipmentRequestService().cancel(obj, request.user)
        messages.success(request, "Заявка отменена.")
    except ApprovalError as exc:
        messages.error(request, str(exc))

    return redirect("approvals:my_requests")