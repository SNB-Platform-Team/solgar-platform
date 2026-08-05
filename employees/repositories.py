"""
employees app — data access layer.

The only place employee records are queried. ORM only, no raw SQL.
"""

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from .models import Employee


class EmployeeRepository:
    """Encapsulates all database access for employees."""

    def all_active(self) -> QuerySet:
        """Return all active employees, ordered by name."""
        return Employee.objects.filter(is_active=True).order_by("full_name")

    def search(self, term: str) -> QuerySet:
        """
        Return active employees matching the term in name, unit, title or email.

        Args:
            term: Free-text search string.

        Returns:
            A filtered, ordered QuerySet.
        """
        qs = self.all_active()
        if not term:
            return qs
        return qs.filter(
            Q(full_name__icontains=term)
            | Q(unit__icontains=term)
            | Q(title__icontains=term)
            | Q(email__icontains=term)
        )

    def get_by_id(self, pk: int) -> Employee:
        """
        Return a single employee by ID, or raise 404 if not found.

        Args:
            pk: The employee's database ID.

        Returns:
            The Employee instance.
        """
        return get_object_or_404(Employee, pk=pk, is_active=True)

    def distinct_units(self) -> list[str]:
        """Return the sorted list of distinct, non-empty unit names."""
        units = (
            Employee.objects.filter(is_active=True)
            .exclude(unit="")
            .values_list("unit", flat=True)
            .distinct()
            .order_by("unit")
        )
        return list(units)

    def distinct_countries(self) -> list[str]:
        """Return the sorted list of distinct, non-empty country names."""
        countries = (
            Employee.objects.filter(is_active=True)
            .exclude(country="")
            .values_list("country", flat=True)
            .distinct()
            .order_by("country")
        )
        return list(countries)

    def distinct_brands(self) -> list[str]:
        """Return the sorted list of distinct, non-empty brand names."""
        brands = (
            Employee.objects.filter(is_active=True)
            .exclude(brand="")
            .values_list("brand", flat=True)
            .distinct()
            .order_by("brand")
        )
        return list(brands)