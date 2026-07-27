"""
employees app — business logic layer.

Views call services; services call the repository. Keeps query logic
out of the views and business rules in one place.
"""

from django.db.models import QuerySet

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