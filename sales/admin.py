"""sales app — admin registration."""

from django.contrib import admin

from .models import BrandDefinition, ChainDefinition, DistributorRecord, SalesRecord, DadQuery


@admin.register(BrandDefinition)
class BrandDefinitionAdmin(admin.ModelAdmin):
    """Manage parametric brand definitions."""

    list_display = ("name", "code", "priority", "is_default", "is_active")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "code")
    ordering = ("priority", "name")

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

    list_display = ("name", "source_type", "country", "orientation", "is_active")
    list_filter = ("source_type", "country", "orientation", "is_active")
    search_fields = ("name",)  


@admin.register(DistributorRecord)
class DistributorRecordAdmin(admin.ModelAdmin):
    """Inspect uploaded distributor sales/stock records."""

    list_display = (
        "distributor", "operation_type", "product_name", "brand",
        "count", "amount", "city", "begin_date", "end_date",
    )
    list_filter = ("operation_type", "distributor", "brand", "country")
    search_fields = ("product_name", "client", "city", "inn")
    date_hierarchy = "begin_date"
    ordering = ("-begin_date", "distributor")


@admin.register(DadQuery)
class DadQueryAdmin(admin.ModelAdmin):
    """
    Admin for the SQL script store (mirrors Java's solgar_gen.dad_queries).
 
    Lets managers view, edit, and add report SQL fragments from one place
    without touching code. The query_script is the raw SQL fragment; edit
    with care since the Sales Report screen depends on these.
    """
 
    list_display = ("query_name", "short_description", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("query_name", "query_script", "description")
    readonly_fields = ("updated_at",)
    ordering = ("query_name",)
    list_per_page = 50
 
    fieldsets = (
        (None, {
            "fields": ("query_name", "description", "is_active"),
        }),
        ("SQL", {
            "fields": ("query_script",),
            "description": "Raw SQL fragment. The Sales Report screen combines "
                           "these with generated SELECT/pivot/filter clauses.",
        }),
        ("Meta", {
            "fields": ("updated_at",),
            "classes": ("collapse",),
        }),
    )
 
    def short_description(self, obj):
        """Truncated description for the list view."""
        text = obj.description or (obj.query_script or "")
        return (text[:60] + "...") if len(text) > 60 else text
 
    short_description.short_description = "Описание / SQL"
 


# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# |   |——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# |   |————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# |   |——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————