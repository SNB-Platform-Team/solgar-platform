"""authorization app — admin registration for screens and access levels."""

from django import forms
from django.contrib import admin

from .models import AccessLevel, Document, Screen


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

class DocumentAdminForm(forms.ModelForm):
    """Yonetici bir PDF dosyasi secer; icerik DB'ye (BinaryField) yazilir."""

    pdf_file = forms.FileField(
        label="PDF файл",
        required=False,
        help_text="Загрузите PDF. При редактировании оставьте пустым, чтобы сохранить текущий файл.",
    )

    class Meta:
        model = Document
        fields = ("title", "order", "is_active")

    def save(self, commit=True):
        obj = super().save(commit=False)
        f = self.cleaned_data.get("pdf_file")
        if f is not None:
            data = f.read()
            obj.content = data
            obj.size = len(data)
            obj.content_type = getattr(f, "content_type", "") or "application/pdf"
        if commit:
            obj.save()
        return obj

    def clean(self):
        cleaned = super().clean()
        # Yeni kayitta dosya zorunlu; duzenlemede bos birakilabilir (mevcut korunur).
        if self.instance.pk is None and not cleaned.get("pdf_file"):
            self.add_error("pdf_file", "Для нового документа загрузите PDF-файл.")
        return cleaned


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """FAQ dokumanlarini yonet (PDF yukle, sira, aktiflik)."""

    form = DocumentAdminForm
    list_display = ("title", "order", "is_active", "size", "uploaded_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    ordering = ("order", "title")
