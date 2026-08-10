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

from .models import ChainDefinition, DistributorRecord, SalesRecord
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
        "chains": list(
            ChainDefinition.objects.filter(is_active=True).values_list("name", flat=True)
        ),
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

    # Find the parse definition for the selected chain.
    try:
        definition = ChainDefinition.objects.get(name=chain_name, is_active=True)
    except ChainDefinition.DoesNotExist:
        messages.error(request, f"Определение для сети «{chain_name}» не найдено.")
        return render(request, "sales/upload.html", context)

    service = SalesUploadService()
    try:
        result = service.preview(excel_file, definition, excel_file.name)
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

@login_required
@require_screen("SALES_VIEW")
@require_http_methods(["GET"])
def sales_export_view(request: HttpRequest) -> HttpResponse:
    """Export the filtered sales records as an .xlsx download."""
    from io import BytesIO

    service = SalesViewService()

    # Same filter parsing as the report view.
    filters: dict[str, Any] = {}
    report_date_str = request.GET.get("report_date", "").strip()
    if report_date_str:
        try:
            filters["report_date"] = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    for key in ("chain_name", "country", "brand", "city"):
        value = request.GET.get(key, "").strip()
        if value:
            filters[key] = value
    search = request.GET.get("q", "").strip()
    if search:
        filters["search"] = search

    wb = service.export_to_excel(**filters)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="sales_export.xlsx"'
    return response

@login_required
@require_screen("SALES_CHAIN")
@require_http_methods(["GET"])
def sales_chain_report_view(request: HttpRequest) -> HttpResponse:
    """
    Pharmacy chain sales report — Java 'Sales Report Observation' equivalent.
    Date-range filtering by company type (brand), chain, country, city.
    """
    service = SalesViewService()

    filters: dict[str, Any] = {}

    date_from_str = request.GET.get("date_from", "").strip()
    date_to_str = request.GET.get("date_to", "").strip()
    if date_from_str:
        try:
            filters["date_from"] = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if date_to_str:
        try:
            filters["date_to"] = datetime.strptime(date_to_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    for key in ("chain_name", "country", "brand", "city"):
        value = request.GET.get(key, "").strip()
        if value:
            filters[key] = value
    search = request.GET.get("q", "").strip()
    if search:
        filters["search"] = search

    report = service.chain_report(**filters)
    options = service.filter_options()

    context: dict[str, Any] = {
        "report": report,
        "records": report["records"][:500],
        "options": options,
        "countries": COUNTRIES,
        "brands": SalesRecord.Brand.choices,
        "f_date_from": date_from_str,
        "f_date_to": date_to_str,
        "f_chain": request.GET.get("chain_name", ""),
        "f_country": request.GET.get("country", ""),
        "f_brand": request.GET.get("brand", ""),
        "f_city": request.GET.get("city", ""),
        "f_search": request.GET.get("q", ""),
        "has_query": bool(request.GET),
    }
    return render(request, "sales/chain_report.html", context)


DISTRIBUTOR_SESSION_KEY = "distributor_preview"


@login_required
@require_screen("DIST_UPLOAD")
@require_http_methods(["GET", "POST"])
def distributor_upload_view(request: HttpRequest) -> HttpResponse:
    """Upload a distributor sales/stock Excel, preview, then save."""
    distributors = list(
        ChainDefinition.objects.filter(
            is_active=True, source_type=ChainDefinition.SourceType.DISTRIBUTOR
        ).values_list("name", flat=True)
    )

    context: dict[str, Any] = {
        "distributors": distributors,
        "countries": COUNTRIES,
        "operations": DistributorRecord.Operation.choices,
    }

    if request.method == "GET":
        return render(request, "sales/distributor_upload.html", context)

    action = request.POST.get("action", "preview")

    # SAVE — read parsed rows from session.
    if action == "save":
        stashed = request.session.get(DISTRIBUTOR_SESSION_KEY)
        if not stashed:
            messages.error(request, "Данные не найдены. Загрузите файл заново.")
            return render(request, "sales/distributor_upload.html", context)

        begin_date = (
            datetime.strptime(stashed["begin_date"], "%Y-%m-%d").date()
            if stashed["begin_date"] else None
        )
        end_date = (
            datetime.strptime(stashed["end_date"], "%Y-%m-%d").date()
            if stashed["end_date"] else None
        )
        rows = [
            ParsedRow(
                product_name=r["product_name"], brand=r["brand"],
                pharmacy=r["client"], city=r["city"],
                count=r["count"], amount=Decimal(r["amount"]),
                remaining_count=0, remaining_amount=Decimal("0"),
            )
            for r in stashed["rows"]
        ]
        result = ParseResult(rows=rows)

        created = DistributorUploadService().save_records(
            result, stashed["distributor"], stashed["operation_type"],
            stashed["country"], begin_date, end_date, request.user,
        )
        request.session.pop(DISTRIBUTOR_SESSION_KEY, None)
        messages.success(request, f"Сохранено записей: {created}.")
        return redirect("sales:distributor_upload")

    # PREVIEW
    distributor = request.POST.get("distributor", "").strip()
    operation_type = request.POST.get("operation_type", "").strip()
    country = request.POST.get("country", "").strip()
    begin_date_str = request.POST.get("begin_date", "").strip()
    end_date_str = request.POST.get("end_date", "").strip()
    excel_file = request.FILES.get("excel_file")

    context.update({
        "selected_distributor": distributor,
        "selected_operation": operation_type,
        "selected_country": country,
        "begin_date": begin_date_str,
        "end_date": end_date_str,
    })

    if not excel_file:
        messages.error(request, "Выберите файл Excel.")
        return render(request, "sales/distributor_upload.html", context)
    if not distributor or not operation_type or not country:
        messages.error(request, "Заполните дистрибьютора, тип операции и страну.")
        return render(request, "sales/distributor_upload.html", context)

    try:
        definition = ChainDefinition.objects.get(
            name=distributor, is_active=True,
            source_type=ChainDefinition.SourceType.DISTRIBUTOR,
        )
    except ChainDefinition.DoesNotExist:
        messages.error(request, f"Определение для «{distributor}» не найдено.")
        return render(request, "sales/distributor_upload.html", context)

    try:
        result = DistributorUploadService().preview(
            excel_file, definition, excel_file.name
        )
    except SalesParseError as exc:
        messages.error(request, str(exc))
        return render(request, "sales/distributor_upload.html", context)

    if result.total_rows == 0:
        messages.error(request, "В файле не найдено данных.")
        return render(request, "sales/distributor_upload.html", context)

    request.session[DISTRIBUTOR_SESSION_KEY] = {
        "distributor": distributor, "operation_type": operation_type,
        "country": country, "begin_date": begin_date_str, "end_date": end_date_str,
        "rows": [
            {
                "product_name": r.product_name, "brand": r.brand,
                "client": r.pharmacy, "city": r.city,
                "count": r.count, "amount": str(r.amount),
            }
            for r in result.rows
        ],
    }

    context.update({"result": result, "rows": result.rows, "preview": True})
    return render(request, "sales/distributor_upload.html", context)