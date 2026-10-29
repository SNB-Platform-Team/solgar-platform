"""
authorization app — screen-based access levels.

Defines the screens (pages/modules) in the platform and the access levels
that determine which screens each user may see. This is separate from the
organizational hierarchy: access level governs *what a user can see*, not
*who reports to whom*.
"""

from django.db import models


class Screen(models.Model):
    """A single screen (page or module) that access can be granted to."""

    code = models.CharField("Screen code", max_length=50, unique=True)
    name = models.CharField("Display name", max_length=120)
    description = models.CharField("Description", max_length=255, blank=True)
    is_active = models.BooleanField("Is active", default=True)
    order = models.PositiveIntegerField("Menu order", default=0)

    class Meta:
        verbose_name = "Screen"
        verbose_name_plural = "Screens"
        db_table = "authorization_screen"
        ordering = ["order", "name"]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.code} — {self.name}"


class AccessLevel(models.Model):
    """
    An access level grouping a set of screens.

    `rank` is a numeric ordering (higher = more access), useful for
    comparisons like "at least manager level". Screens are assigned
    explicitly via the many-to-many relation.
    """

    name = models.CharField("Level name", max_length=80, unique=True)
    rank = models.PositiveIntegerField("Rank", default=1)
    description = models.CharField("Description", max_length=255, blank=True)
    screens = models.ManyToManyField(
        Screen,
        related_name="access_levels",
        blank=True,
        verbose_name="Accessible screens",
    )

    class Meta:
        verbose_name = "Access level"
        verbose_name_plural = "Access levels"
        db_table = "authorization_access_level"
        ordering = ["rank", "name"]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.name} (rank {self.rank})"

    def screen_codes(self) -> set[str]:
        """Return the set of active screen codes this level can access."""
        return set(
            self.screens.filter(is_active=True).values_list("code", flat=True)
        )

class Document(models.Model):
    """
    FAQ sayfasinda kullanicilara sunulan PDF dokumani (kullanim talimatlari).

    Yonetici /admin'den yukler; FAQ API'si aktif dokumanlari listeler ve
    kullanici tarayicida acar. PDF icerigi DB'de (BinaryField) saklanir, ciplak
    dosya sisteminde degil: Azure App Service diski deploy'da sifirlandigi icin
    dosya tabanli depolama kalici degil. DB (Sber MySQL) kalici.
    """

    title = models.CharField("Название", max_length=200)
    # PDF'in ikili icerigi (DB'de kalici). Yukleme ModelAdmin'de bir dosya
    # alanindan okunup buraya yazilir (bkz. authorization/admin.py).
    content = models.BinaryField("PDF содержимое", editable=False)
    content_type = models.CharField(
        "MIME", max_length=100, default="application/pdf", editable=False
    )
    size = models.PositiveIntegerField("Размер (байт)", default=0, editable=False)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)
    uploaded_at = models.DateTimeField("Загружено", auto_now=True)

    class Meta:
        verbose_name = "Документ (FAQ)"
        verbose_name_plural = "Документы (FAQ)"
        db_table = "authorization_document"
        ordering = ["order", "title"]

    def __str__(self) -> str:
        return self.title
