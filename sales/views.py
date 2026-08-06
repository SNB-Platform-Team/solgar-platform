"""sales app — views for uploading and viewing chain sales data."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from authorization.decorators import require_screen

from .models import SalesRecord
from .services import (
    ParsedRow, ParseResult, SalesParseError, SalesUploadService, SalesViewService,
)
CHAINS = ["MFO"]
COUNTRIES = ["Russia", "Kazakhstan", "Belarus", "Uzbekistan", "Azerbaijan"]

SESSION_KEY = "sales_preview"


@login_required
@require_screen("SALES_UPLOAD")
@require_http_methods(["GET", "POST"])
def sales_upload_view(request: HttpRequest) -> HttpResponse:
    """
    Upload a chain sales Excel file, preview parsed data, then save.

    Preview parses the file and stashes the result in the session; Save reads
    it back from the session, so the user only selects the file once.
    """
    context: dict[str, Any] = {
        "chains": CHAINS,
        "countries": COUNTRIES,
    }

    if request.method == "GET":
        return render(request, "sales/upload.html", context)

    action = request.POST.get("action", "preview")

    # ---- SAVE: read parsed rows from the session, not the file ----
    if action == "save":
        stashed = request.session.get(SESSION_KEY)
        if not stashed:
            messages.error(request, "Данные для сохранения не найдены. Загрузите файл заново.")
            return render(request, "sales/upload.html", context)

        report_date = datetime.strptime(stashed["report_date"], "%Y-%m-%d").date()
        rows = [
            ParsedRow(
                product_name=r["product_name"],
                brand=r["brand"],
                pharmacy=r["pharmacy"],
                city=r["city"],
                count=r["count"],
                amount=Decimal(r["amount"]),
                remaining_count=r["remaining_count"],
                remaining_amount=Decimal(r["remaining_amount"]),
            )
            for r in stashed["rows"]
        ]
        result = ParseResult(rows=rows)

        service = SalesUploadService()
        created = service.save_records(
            result, report_date, stashed["chain_name"], stashed["country"], request.user
        )
        # Clear the stash after saving.
        request.session.pop(SESSION_KEY, None)
        messages.success(request, f"Сохранено записей: {created}.")
        return redirect("sales:upload")

    # ---- PREVIEW: parse the uploaded file ----
    report_date_str = request.POST.get("report_date", "").strip()
    chain_name = request.POST.get("chain_name", "").strip()
    country = request.POST.get("country", "").strip()
    excel_file = request.FILES.get("excel_file")

    context.update({
        "report_date": report_date_str,
        "selected_chain": chain_name,
        "selected_country": country,
    })

    if not excel_file:
        messages.error(request, "Выберите файл Excel.")
        return render(request, "sales/upload.html", context)
    if not report_date_str or not chain_name or not country:
        messages.error(request, "Заполните дату, сеть и страну.")
        return render(request, "sales/upload.html", context)

    try:
        report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Неверный формат даты (ГГГГ-ММ-ДД).")
        return render(request, "sales/upload.html", context)

    service = SalesUploadService()
    try:
                result = service.preview(excel_file, excel_file.name)
    except SalesParseError as exc:
        messages.error(request, str(exc))
        return render(request, "sales/upload.html", context)

    if result.total_rows == 0:
        messages.error(request, "В файле не найдено ни одной строки с данными.")
        return render(request, "sales/upload.html", context)

    # Stash the parsed result in the session for the subsequent save.
    request.session[SESSION_KEY] = {
        "report_date": report_date_str,
        "chain_name": chain_name,
        "country": country,
        "rows": [
            {
                "product_name": row.product_name,
                "brand": row.brand,
                "pharmacy": row.pharmacy,
                "city": row.city,
                "count": row.count,
                "amount": str(row.amount),
                "remaining_count": row.remaining_count,
                "remaining_amount": str(row.remaining_amount),
            }
            for row in result.rows
        ],
    }

    context.update({
        "result": result,
        "rows": result.rows,
        "preview": True,
    })
    return render(request, "sales/upload.html", context)


@login_required
@require_screen("SALES_VIEW")
@require_http_methods(["GET"])
def sales_report_view(request: HttpRequest) -> HttpResponse:
    """View saved sales data with server-side filtering and brand totals."""
    service = SalesViewService()

    # Read filters from the query string.
    report_date_str = request.GET.get("report_date", "").strip()
    chain_name = request.GET.get("chain_name", "").strip()
    country = request.GET.get("country", "").strip()
    brand = request.GET.get("brand", "").strip()
    city = request.GET.get("city", "").strip()
    search = request.GET.get("q", "").strip()

    filters: dict[str, Any] = {}
    if report_date_str:
        try:
            filters["report_date"] = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if chain_name:
        filters["chain_name"] = chain_name
    if country:
        filters["country"] = country
    if brand:
        filters["brand"] = brand
    if city:
        filters["city"] = city
    if search:
        filters["search"] = search

    result = service.query(**filters)
    options = service.filter_options()

    context: dict[str, Any] = {
        "result": result,
        "records": result["records"][:500],  # cap display for performance
        "options": options,
        "countries": COUNTRIES,
        "brands": SalesRecord.Brand.choices,
        # echo back selected filters
        "f_report_date": report_date_str,
        "f_chain": chain_name,
        "f_country": country,
        "f_brand": brand,
        "f_city": city,
        "f_search": search,
    }
    return render(request, "sales/report.html", context)