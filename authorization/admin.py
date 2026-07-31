"""authorization app — admin registration for screens and access levels."""

from django.contrib import admin

from .models import AccessLevel, Screen


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    """Manage the screens that access can be granted to."""

    list_display = ("code", "name", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("order", "name")


@admin.register(AccessLevel)
class AccessLevelAdmin(admin.ModelAdmin):
    """Manage access levels and the screens each one can see."""

    list_display = ("name", "rank")
    ordering = ("rank", "name")
    filter_horizontal = ("screens",)