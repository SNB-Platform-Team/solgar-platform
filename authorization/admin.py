"""authorization app — admin registration for screens and access levels."""

from django import forms
from django.contrib import admin

from .models import AccessLevel, Document, DocumentCategory, Screen


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

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """FAQ dokuman klasorleri (Marketing, HR, ...)."""

    list_display = ("name", "order", "is_active", "doc_count")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("order", "name")

    def doc_count(self, obj):
        return obj.documents.count()
    doc_count.short_description = "Документов"


class DocumentAdminForm(forms.ModelForm):
    """Yonetici bir dosya secer; icerik DB'ye (BinaryField) yazilir. Her tur
    dosya kabul edilir (PDF/Office/resim/zip...). MIME ve dosya adi dosyadan."""

    upload_file = forms.FileField(
        label="Файл",
        required=False,
        help_text="Загрузите файл (PDF, Word, Excel, изображение и т.д.). "
                  "При редактировании оставьте пустым, чтобы сохранить текущий файл.",
    )

    class Meta:
        model = Document
        fields = ("category", "title", "order", "is_active")

    def save(self, commit=True):
        obj = super().save(commit=False)
        f = self.cleaned_data.get("upload_file")
        if f is not None:
            import mimetypes
            data = f.read()
            obj.content = data
            obj.size = len(data)
            name = getattr(f, "name", "") or ""
            obj.original_name = name
            # MIME: once tarayicidan gelen, yoksa uzantidan tahmin.
            ct = getattr(f, "content_type", "") or ""
            if not ct or ct == "application/octet-stream":
                guessed, _ = mimetypes.guess_type(name)
                ct = guessed or ct or "application/octet-stream"
            obj.content_type = ct
        if commit:
            obj.save()
        return obj

    def clean(self):
        cleaned = super().clean()
        # Yeni kayitta dosya zorunlu; duzenlemede bos birakilabilir (mevcut korunur).
        if self.instance.pk is None and not cleaned.get("upload_file"):
            self.add_error("upload_file", "Для нового документа загрузите файл.")
        return cleaned


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """FAQ dokumanlarini yonet (dosya yukle, klasore ata, sira, aktiflik)."""

    form = DocumentAdminForm
    list_display = ("title", "category", "order", "is_active", "content_type",
                    "size", "uploaded_at")
    list_filter = ("is_active", "category")
    search_fields = ("title", "original_name")
    ordering = ("category", "order", "title")
