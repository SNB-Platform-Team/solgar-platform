"""employees app — views for the employee directory."""

from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .services import EmployeeService


@login_required
def employee_list_view(request: HttpRequest) -> HttpResponse:
    """Render the employee directory with optional search."""
    search_term: str = request.GET.get("q", "")
    employees = EmployeeService().list_employees(search_term)

    context: dict[str, Any] = {
        "employees": employees,
        "search_term": search_term,
        "total": employees.count(),
    }
    return render(request, "employees/list.html", context)