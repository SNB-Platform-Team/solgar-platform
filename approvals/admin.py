"""approvals app — admin registration for equipment requests."""

from django.contrib import admin

from .models import EquipmentRequest


@admin.register(EquipmentRequest)
class EquipmentRequestAdmin(admin.ModelAdmin):
    """Manage and inspect equipment requests."""

    list_display = ("item", "requester", "approver", "status", "created_at", "decided_at")
    list_filter = ("status", "created_at")
    search_fields = ("item", "requester__username", "approver__username")
    readonly_fields = ("created_at", "decided_at")