"""
employees app — employee directory model.

Stores the company staff list shown under the "Organization" menu.
Populated from an imported file; all access goes through the ORM.
"""

from django.db import models


class Employee(models.Model):
    """A single company employee shown in the directory."""

    full_name = models.CharField("Full name", max_length=200)
    unit = models.CharField("Unit / Department", max_length=200, blank=True)
    title = models.CharField("Job title", max_length=200, blank=True)
    email = models.EmailField("Email", max_length=254, blank=True)
    activation_date = models.DateField("Activation date", null=True, blank=True)
    region = models.CharField("Region", max_length=100, blank=True)
    country = models.CharField("Country", max_length=100, blank=True)
    brand = models.CharField("Brand", max_length=100, blank=True)
    is_active = models.BooleanField("Is active", default=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        db_table = "employees_employee"
        ordering = ["full_name"]

    def __str__(self) -> str:
        """Readable representation for admin and logs."""
        return self.full_name