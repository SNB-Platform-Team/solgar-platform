"""sales app — admin registration."""

from django.contrib import admin

from .models import ChainDefinition, SalesRecord


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    """Inspect uploaded sales records."""

    list_display = (
        "product_name", "brand", "chain_name", "report_date",
        "city", "count", "amount", "remaining_count",
    )
    list_filter = ("brand", "chain_name", "country", "report_date")
    search_fields = ("product_name", "city", "pharmacy")
    date_hierarchy = "report_date"
    ordering = ("-report_date", "product_name")


@admin.register(ChainDefinition)
class ChainDefinitionAdmin(admin.ModelAdmin):
    """Manage parametric chain parse definitions."""

    list_display = ("name", "country", "orientation", "is_active")
    list_filter = ("country", "orientation", "is_active")
    search_fields = ("name",)