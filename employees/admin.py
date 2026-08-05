"""employees app — admin registration."""

from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin configuration for the Employee model."""

    list_display = ("full_name", "unit", "title", "email", "region", "country", "brand", "is_active")
    list_filter = ("unit", "is_active", "region", "country", "brand")
    search_fields = ("full_name", "email", "unit", "title")
    ordering = ("full_name",)