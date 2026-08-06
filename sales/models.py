"""
sales app — pharmacy chain sales data.

Sales records are uploaded from chain Excel files, one row per product line.
Each record is classified as Solgar or Bounty based on the product name.
"""

from django.conf import settings
from django.db import models


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