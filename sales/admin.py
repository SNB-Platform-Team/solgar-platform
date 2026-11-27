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
 



from .models import GeocodeSettings


@admin.register(GeocodeSettings)
class GeocodeSettingsAdmin(admin.ModelAdmin):
    list_display = ("provider", "is_active", "updated_at")
    fields = ("provider", "is_active", "dadata_key", "dadata_secret", "yandex_key")

from django.utils.html import format_html
from .models import PharmacyEquipment, PharmacyEquipmentPhoto


class PharmacyEquipmentPhotoInline(admin.TabularInline):
    model = PharmacyEquipmentPhoto
    extra = 0
    # Onizleme (thumbnail) + "Открыть" linki: gorseli admin'den acip bakmak
    # icin (alakasiz/yanlis foto kontrolu). SAS url 60 dk gecerli.
    readonly_fields = ("preview", "open_link", "original_name", "content_type",
                       "size", "blob_name", "created_at")
    fields = ("preview", "open_link", "original_name", "content_type", "size",
              "blob_name", "created_at")
    can_delete = True

    def _sas(self, obj):
        """blob_name icin 60 dk'lik SAS url (blob yapilandirilmamissa None)."""
        try:
            from sales import blob_storage as _blob
            if obj and obj.blob_name and _blob.blob_configured():
                return _blob.get_sas_url(obj.blob_name, minutes=60)
        except Exception:
            return None
        return None

    @admin.display(description="Превью")
    def preview(self, obj):
        url = self._sas(obj)
        if not url:
            return "—"
        # content_type gorsel degilse ( or. pdf) kucuk resim yerine not.
        ct = (getattr(obj, "content_type", "") or "").lower()
        if ct.startswith("image/"):
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:120px;'
                'border:1px solid #ccc;border-radius:4px" />', url)
        return format_html('<span>{}</span>', ct or "файл")

    @admin.display(description="Открыть")
    def open_link(self, obj):
        url = self._sas(obj)
        if not url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Открыть ↗</a>', url)


@admin.register(PharmacyEquipment)
class PharmacyEquipmentAdmin(admin.ModelAdmin):
    """Platformun kendi ekipman kayitlari (оборудование). Fotolar Azure Blob'da.

    Her kayitta: hangi eczane (pharmacy_id), marka, promo/подтип, KIM ekledi
    (created_by), NE ZAMAN (created_at) ve fotolar (inline: orijinal dosya adi
    + onizleme + 'Открыть' linki ile gorseli acip kontrol). Yonetici alakasiz/
    yanlis yuklenmis gorselleri buradan gorebilir."""

    list_display = ("id", "pharmacy_id", "brand", "promo", "subtype", "size",
                    "status", "photo_count", "created_by", "created_at")
    list_filter = ("brand", "status", "promo")
    search_fields = ("pharmacy_id", "promo", "subtype", "created_by")
    ordering = ("-created_at",)
    inlines = [PharmacyEquipmentPhotoInline]

    @admin.display(description="Фото")
    def photo_count(self, obj):
        return obj.photos.count() if hasattr(obj, "photos") else 0
