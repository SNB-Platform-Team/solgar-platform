"""accounts app — admin registration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = ("username", "email", "user_type", "department", "is_enabled", "is_staff")
    list_filter = ("user_type", "is_enabled", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Solgar Platform",
            {"fields": ("user_type", "azure_object_id", "department", "phone", "is_enabled")},
        ),
    )