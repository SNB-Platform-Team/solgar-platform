"""
sales app — pharmacy chain sales data.

Sales records are uploaded from chain Excel files, one row per product line.
Each record is classified as Solgar or Bounty based on the product name.
"""

from django.conf import settings
from django.db import models

class BrandDefinition(models.Model):
    """
    Parametric brand definition. Instead of hard-coding brand keywords in
    the parser, each brand's markers live here. Deactivating a brand
    ('pulling it out') is a data change, not a code change.
    """

    name = models.CharField("Brand name", max_length=80, unique=True)
    code = models.CharField("Brand code", max_length=20, unique=True)

    # Keywords that identify this brand in a product name (case-insensitive,
    # apostrophes normalised). e.g. ["natures bounty", "нэйчес", "нб"]
    keywords = models.JSONField("Keywords", default=list)

    # If no active brand's keywords match, the product is assigned to the
    # brand marked as default. Exactly one brand should be default.
    is_default = models.BooleanField("Default brand", default=False)

    # Lower priority number is checked first when matching keywords.
    priority = models.IntegerField("Priority", default=100)

    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Brand definition"
        verbose_name_plural = "Brand definitions"
        db_table = "intern_sls_brand_definition"
        ordering = ["priority", "name"]

    def __str__(self) -> str:
        """Readable representation."""
        flags = []
        if self.is_default:
            flags.append("default")
        if not self.is_active:
            flags.append("inactive")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.name}{suffix}"


class ChainDefinition(models.Model):
    """
    Parametric definition of how to parse one chain/distributor's Excel.

    Instead of a separate parser per chain, a single parser reads these
    definitions. Adding a new chain means adding a row here, not new code.
    """

    class Orientation(models.TextChoices):
        """Excel layout: rows stacked vertically or spread horizontally."""

        VERTICAL = "VERTICAL", "Вертикальный"
        HORIZONTAL = "HORIZONTAL", "Горизонтальный"

    name = models.CharField("Chain / distributor name", max_length=120, unique=True)
    country = models.CharField("Country", max_length=60, default="Russia")
    orientation = models.CharField(
        "Layout orientation", max_length=12,
        choices=Orientation.choices, default=Orientation.VERTICAL,
    )

    # Maps logical fields to the Excel header text for this chain, e.g.
    # {"product": "Номенклатура", "count": "Продажи", "amount": "Сумма в руб.",
    #  "city": "Город", "pharmacy": "Адрес грузополучателя",
    #  "remaining_count": "Остаток на конец периода"}
    # Only "product" and "count" are strictly required.
    column_map = models.JSONField("Column mapping", default=dict)

    # How many rows from the top to scan when locating the header row.
    header_search_limit = models.IntegerField("Header search limit", default=30)

    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Chain definition"
        verbose_name_plural = "Chain definitions"
        db_table = "intern_sls_chain_definition"
        ordering = ["name"]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.name} ({self.country}, {self.get_orientation_display()})"




class SalesRecord(models.Model):
    """A single product sales line from a chain's Excel report."""

    class Brand(models.TextChoices):
        """Which brand the product belongs to."""

        SOLGAR = "SOLGAR", "Solgar"
        BOUNTY = "BOUNTY", "Nature's Bounty"
        OTHER = "OTHER", "Other"

    # Upload context
    report_date = models.DateField("Report date")
    chain_name = models.CharField("Chain name", max_length=120)
    country = models.CharField("Country", max_length=60)

    # Product line data (from Excel)
    product_name = models.CharField("Product name", max_length=300)
    brand = models.CharField(
        "Brand", max_length=10, choices=Brand.choices, default=Brand.OTHER
    )
    pharmacy = models.CharField("Pharmacy / address", max_length=400, blank=True)
    city = models.CharField("City", max_length=150, blank=True)
    count = models.IntegerField("Sales count", default=0)
    amount = models.DecimalField("Sales amount", max_digits=14, decimal_places=2, default=0)
    remaining_count = models.IntegerField("Remaining stock count", default=0)
    remaining_amount = models.DecimalField(
        "Remaining stock amount", max_digits=14, decimal_places=2, default=0
    )

    # Bookkeeping
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_uploads",
        verbose_name="Uploaded by",
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Sales record"
        verbose_name_plural = "Sales records"
        db_table = "sales_record"
        ordering = ["-report_date", "chain_name", "product_name"]
        indexes = [
            models.Index(fields=["report_date", "chain_name"]),
            models.Index(fields=["brand"]),
        ]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.product_name} — {self.count} ({self.get_brand_display()})"