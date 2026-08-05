"""
employees app — business logic layer.

Views call services; services call the repository.
"""

from django.db.models import QuerySet

from .models import Employee
from .repositories import EmployeeRepository


class EmployeeService:
    """Business operations for the employee directory."""

    def __init__(self) -> None:
        """Wire up the repository dependency."""
        self.repository = EmployeeRepository()

    def list_employees(self, search_term: str = "") -> QuerySet:
        """
        Return employees for the directory, optionally filtered by search.

        Args:
            search_term: Optional free-text filter.

        Returns:
            A QuerySet of active employees.
        """
        return self.repository.search(search_term.strip())

    def get_employee(self, pk: int) -> Employee:
        """
        Return a single employee by primary key.

        Args:
            pk: The employee's database ID.

        Returns:
            The Employee instance.
        """
        return self.repository.get_by_id(pk)

    def list_units(self) -> list[str]:
        """Return the distinct unit names for the filter dropdown."""
        return self.repository.distinct_units()

    def list_countries(self) -> list[str]:
        """Return the distinct country names for the filter dropdown."""
        return self.repository.distinct_countries()

    def list_brands(self) -> list[str]:
        """Return the distinct brand names for the filter dropdown."""
        return self.repository.distinct_brands()