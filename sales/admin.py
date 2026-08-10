"""sales app — admin registration."""

from django.contrib import admin

from .models import BrandDefinition, ChainDefinition, DistributorRecord, SalesRecord

from .models import BrandDefinition, ChainDefinition, SalesRecord

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



# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# |   |——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# |   |————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# |   |——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————