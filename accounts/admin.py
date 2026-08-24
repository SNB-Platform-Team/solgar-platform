"""accounts app — admin registration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = ("username", "email", "user_type", "access_level", "department", "is_enabled", "is_staff")
    list_filter = ("user_type", "is_enabled", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Solgar Platform",
            {"fields": ("user_type", "access_level", "manager", "azure_object_id", "department", "phone", "is_enabled")},
        ),
    )


from .models import LoginLog, ActivityLog

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    """Read-only view of login/logout audit records."""

    list_display = ("user", "event_type", "ip_address", "timestamp")
    list_filter = ("event_type", "timestamp")
    search_fields = ("user__username", "ip_address")
    readonly_fields = ("user", "event_type", "ip_address", "user_agent", "timestamp")
    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        """Logs are created by the system, not manually."""
        return False

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Read-only admin view of user activity."""

    list_display = ("timestamp", "user", "action_type", "screen", "method", "path", "ip_address")
    list_filter = ("action_type", "method", "timestamp", "user")
    search_fields = ("user__username", "path", "screen", "detail")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
    list_per_page = 50

    def has_add_permission(self, request):
        """Activity logs are written by middleware, not added by hand."""
        return False

    def has_change_permission(self, request, obj=None):
        """Logs are immutable."""
        return False
