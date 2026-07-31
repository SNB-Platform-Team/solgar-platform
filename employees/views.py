"""employees app — views for the employee directory."""

from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from authorization.decorators import require_screen

from .services import EmployeeService


@login_required
@require_screen("EMPLOYEES")
def employee_list_view(request: HttpRequest) -> HttpResponse:
    """Render the employee directory with optional search."""
    search_term: str = request.GET.get("q", "")
    service = EmployeeService()
    employees = service.list_employees(search_term)

    context: dict[str, Any] = {
        "employees": employees,
        "search_term": search_term,
        "total": employees.count(),
        "units": service.list_units(),
    }
    return render(request, "employees/list.html", context)


@login_required
@require_screen("EMPLOYEES")
def employee_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Render a single employee's details."""
    employee = EmployeeService().get_employee(pk)
    return render(request, "employees/detail.html", {"employee": employee})