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
    DistributorUploadService, DistributorViewService, ParsedRow, ParseResult,
    SalesParseError, SalesUploadService, SalesViewService,
)
CHAINS = ["MFO"]
COUNTRIES = ["Russia", "Kazakhistan", "Belarusian", "Uzbekistan", "Azerbaijan",
    "Kyrgystan", "Armenia", "Tajikistan",]
DOCTOR_CATEGORIES = ["A+", "A", "B", "C"]
DOCTOR_ACTIVENESS = ["Актив", "Не Актив", "в процессе"]
CLINIC_STATUSES = ["GOLD", "PLATINUM", "SILVER"]
DOCTOR_BRANDS = ["SOLGAR", "NATURES BOUNTY", "OBF"]


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
    options = service.filter_options(country=request.GET.get("country", ""))

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

    # Category and geographic filters (resolved via reference data).
    main_group = request.GET.get("main_group", "").strip()
    sub_group = request.GET.get("sub_group", "").strip()
    region = request.GET.get("region", "").strip()
    district = request.GET.get("district", "").strip()

    report = service.chain_report(
        main_group=main_group, sub_group=sub_group,
        region=region, district=district, **filters
    )
    options = service.filter_options(country=request.GET.get("country", ""))

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
        "f_main_group": main_group,
        "f_sub_group": sub_group,
        "f_region": region,
        "f_district": district,
        "has_query": bool(request.GET),
    }
    return render(request, "sales/chain_report.html", context)

@login_required
@require_screen("SALES_CHAIN")
@require_http_methods(["GET"])
def chain_filter_options_json(request: HttpRequest) -> HttpResponse:
    """
    AJAX endpoint: return chain/region/district options for a given country.

    Called by the chain report page when the user changes the country
    dropdown, so the dependent dropdowns (Сеть, Регион, Округ) refresh
    without a full page reload. Mirrors the Java country->company cascading,
    driven by ChainDefinition + AddressGroup reference data.
    """
    from django.http import JsonResponse

    country = request.GET.get("country", "").strip()
    service = SalesViewService()
    options = service.filter_options(country=country)
    return JsonResponse({
        "chains": options.get("chains", []),
        "regions": options.get("regions", []),
        "districts": options.get("districts", []),
    })

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


@login_required
@require_screen("DIST_VIEW")
@require_http_methods(["GET"])
def distributor_report_view(request: HttpRequest) -> HttpResponse:
    """View saved distributor sales/stock data with filters — 'Просмотр Сток и Продажа'."""
    service = DistributorViewService()

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
    for key in ("distributor", "operation_type", "country", "brand", "city"):
        value = request.GET.get(key, "").strip()
        if value:
            filters[key] = value
    search = request.GET.get("q", "").strip()
    if search:
        filters["search"] = search

    report = service.query(**filters)
    options = service.filter_options()

    context: dict[str, Any] = {
        "report": report,
        "records": report["records"][:500],
        "options": options,
        "countries": COUNTRIES,
        "brands": DistributorRecord.Brand.choices,
        "operations": DistributorRecord.Operation.choices,
        "f_date_from": date_from_str,
        "f_date_to": date_to_str,
        "f_distributor": request.GET.get("distributor", ""),
        "f_operation": request.GET.get("operation_type", ""),
        "f_country": request.GET.get("country", ""),
        "f_brand": request.GET.get("brand", ""),
        "f_city": request.GET.get("city", ""),
        "f_search": request.GET.get("q", ""),
        "has_query": bool(request.GET),
    }
    return render(request, "sales/distributor_report.html", context)

@login_required
@require_screen("DOCTOR_UPDATE")
@require_http_methods(["GET"])
def doctor_address_options_json(request: HttpRequest) -> HttpResponse:
    """
    AJAX endpoint for the Doctor screen's cascading address dropdowns.

    Returns the option list for one level, narrowed by the levels above it.
    The frontend calls this whenever country/area/region changes, mirroring
    the Java itemStateChanged cascade (country -> area -> region -> city).

    Query params:
        level:   which list to return — "area", "region" or "city".
        country, area, region: the current selections above that level.

    Response: {"options": [...]}  (always sorted, distinct, non-empty)
    """
    from django.http import JsonResponse

    from .repositories import DoctorRepository

    repo = DoctorRepository()
    level = request.GET.get("level", "").strip()
    country = request.GET.get("country", "").strip()
    area = request.GET.get("area", "").strip()
    region = request.GET.get("region", "").strip()

    if level == "area":
        options = repo.areas(country=country)
    elif level == "region":
        options = repo.regions(country=country, area=area)
    elif level == "city":
        options = repo.cities(country=country, area=area, region=region)
    else:
        options = []

    return JsonResponse({"options": options})

@login_required
@require_screen("DOCTOR_UPDATE")
@require_http_methods(["GET"])
def doctor_address_options_json(request: HttpRequest) -> HttpResponse:
    """
    AJAX endpoint for the Doctor screen's cascading address dropdowns.

    Returns the option list for one level, narrowed by the levels above it.
    The frontend calls this whenever country/area/region changes, mirroring
    the Java itemStateChanged cascade (country -> area -> region -> city).

    Query params:
        level:   which list to return — "area", "region" or "city".
        country, area, region: the current selections above that level.
    """
    from django.http import JsonResponse

    from .repositories import DoctorRepository

    repo = DoctorRepository()
    level = request.GET.get("level", "").strip()
    country = request.GET.get("country", "").strip()
    area = request.GET.get("area", "").strip()
    region = request.GET.get("region", "").strip()

    if level == "area":
        options = repo.areas(country=country)
    elif level == "region":
        options = repo.regions(country=country, area=area)
    elif level == "city":
        options = repo.cities(country=country, area=area, region=region)
    else:
        options = []

    return JsonResponse({"options": options})

@login_required
@require_screen("DOCTOR_UPDATE")
@require_http_methods(["GET", "POST"])
def doctor_entry_view(request: HttpRequest) -> HttpResponse:
    """
    Doctor Entry & Update (Врач вход Обновление) — single-page CRUD.
 
    Web port of the Java DoctorEntryUpdate form. The same fields act as both
    search filters (List Doctor) and data-entry inputs (Add/Update). Actions:
 
        list   (GET)  — filter and show the table
        add    (POST) — create a new doctor
        update (POST) — update the selected doctor
        delete (POST) — soft-delete (status=0) the selected doctor
 
    POST actions redirect back (PRG) so a refresh doesn't repeat the write.
    """
    from django.contrib import messages
    from django.shortcuts import redirect, render
 
    from .services import DoctorViewService, DoctorWriteService
 
    view_service = DoctorViewService()
 
    # ---------- POST: write actions ----------
    if request.method == "POST":
        action = request.POST.get("action", "")
        write_service = DoctorWriteService()
        user_name = request.user.get_full_name() or request.user.username
 
        data = {k: v.strip() for k, v in request.POST.items()}
 
        if action == "add":
            try:
                doc = write_service.create(data, user_name=user_name)
                messages.success(request, f"Врач добавлен (ID {doc.id}).")
            except Exception as exc:
                messages.error(request, f"Ошибка при добавлении: {exc}")
 
        elif action == "update":
            doctor_id = request.POST.get("doctor_pk", "").strip()
            if not doctor_id:
                messages.error(request, "Не выбран врач для обновления.")
            else:
                try:
                    n = write_service.update(int(doctor_id), data, user_name=user_name)
                    if n:
                        messages.success(request, "Врач обновлён.")
                    else:
                        messages.error(request, "Врач не найден.")
                except Exception as exc:
                    messages.error(request, f"Ошибка при обновлении: {exc}")
 
        elif action == "delete":
            doctor_id = request.POST.get("doctor_pk", "").strip()
            if not doctor_id:
                messages.error(request, "Не выбран врач для удаления.")
            else:
                try:
                    n = write_service.soft_delete(int(doctor_id))
                    if n:
                        messages.success(request, "Врач удалён.")
                    else:
                        messages.error(request, "Врач не найден.")
                except Exception as exc:
                    messages.error(request, f"Ошибка при удалении: {exc}")
 
        # PRG: filtreleri koruyarak listeye dön
        from urllib.parse import urlencode
        keep = {k: request.POST.get(k, "") for k in (
            "brand", "country", "area", "region", "city", "medrep",
            "specialty", "unified_specialty", "category", "activeness",
            "doctor_name", "clinic_status",
        ) if request.POST.get(k, "")}
        url = request.path
        if keep:
            url = f"{url}?{urlencode(keep)}"
        return redirect(url)
 
    # ---------- GET: filter + list ----------
    filters = {k: request.GET.get(k, "").strip() for k in (
        "brand", "country", "area", "region", "city", "medrep",
        "specialty", "unified_specialty", "category", "activeness",
        "doctor_name", "clinic_status",
    )}
 
    result = view_service.query(**filters)
    options = view_service.address_options(
        country=filters["country"], area=filters["area"], region=filters["region"],
    )
 
    context = {
        "records": result["records"],
        "total_rows": result["total_rows"],
        "options": options,
        "categories": DOCTOR_CATEGORIES,
        "activeness_list": DOCTOR_ACTIVENESS,
        "clinic_statuses": CLINIC_STATUSES,
        "brands": DOCTOR_BRANDS,
        "f": filters,
        "has_query": bool(request.GET),
    }
    return render(request, "sales/doctor_entry.html", context)

# =====================================================================
# PHARMACY (аптека вход Обновление) — sales/views.py sonuna eklendi
# =====================================================================

PHARMACY_BRANDS = ["SOLGAR", "NATURES BOUNTY", "OBF"]
PHARMACY_ACTIVENESS = ["Актив", "Не Актив", "в процессе"]


@login_required
@require_screen("PHARMACY_UPDATE")
@require_http_methods(["GET"])
def pharmacy_options_json(request: HttpRequest) -> HttpResponse:
    """
    AJAX endpoint for the Pharmacy screen's cascading dropdowns. Everything
    is brand-scoped (Solgar/Bounty are separate tables). Levels: area, region,
    city, metro, subchain.
    """
    from django.http import JsonResponse

    from .repositories import PharmacyRepository

    repo = PharmacyRepository()
    brand = request.GET.get("brand", "").strip()
    level = request.GET.get("level", "").strip()
    country = request.GET.get("country", "").strip()
    area = request.GET.get("area", "").strip()
    region = request.GET.get("region", "").strip()
    city = request.GET.get("city", "").strip()
    group_company = request.GET.get("group_company", "").strip()

    if level == "area":
        options = repo.areas(brand, country=country)
    elif level == "region":
        options = repo.regions(brand, country=country, area=area)
    elif level == "city":
        options = repo.cities(brand, country=country, area=area, region=region)
    elif level == "metro":
        options = repo.metros(brand, city=city)
    elif level == "subchain":
        options = repo.subchains(brand, group_company=group_company)
    else:
        options = []

    return JsonResponse({"options": options})


@login_required
@require_screen("PHARMACY_UPDATE")
@require_http_methods(["GET", "POST"])
def pharmacy_entry_view(request: HttpRequest) -> HttpResponse:
    """
    Pharmacy Entry & Update (аптека вход Обновление) - single-page CRUD.

    Web port of the Java PharmacyEntryUpdate form. Brand (SOLGAR / NATURES
    BOUNTY / OBF) is selected first and drives which table is read/written;
    the same fields serve as both search filters and data-entry inputs.
    Actions: list (GET), add / update / delete (POST). PRG on write.
    """
    from django.contrib import messages
    from django.shortcuts import redirect, render

    from .services import (
        PharmacyValidationError, PharmacyViewService, PharmacyWriteService,
    )

    view_service = PharmacyViewService()
    brand = (request.GET.get("brand") or request.POST.get("brand") or "SOLGAR").strip()

    if request.method == "POST":
        action = request.POST.get("action", "")
        write_service = PharmacyWriteService()
        user_name = request.user.get_full_name() or request.user.username
        data = {k: v.strip() for k, v in request.POST.items()}

        try:
            if action == "add":
                obj = write_service.create(brand, data, user_name=user_name)
                messages.success(request, f"Аптека добавлена (ID {obj.id}).")
            elif action == "update":
                pk = request.POST.get("pharmacy_pk", "").strip()
                if not pk:
                    messages.error(request, "Не выбрана аптека для обновления.")
                else:
                    n = write_service.update(brand, int(pk), data, user_name=user_name)
                    messages.success(request, "Аптека обновлена." if n else "Аптека не найдена.")
            elif action == "delete":
                pk = request.POST.get("pharmacy_pk", "").strip()
                if not pk:
                    messages.error(request, "Не выбрана аптека для удаления.")
                else:
                    n = write_service.soft_delete(brand, int(pk))
                    messages.success(request, "Аптека удалена." if n else "Аптека не найдена.")
        except PharmacyValidationError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f"Ошибка: {exc}")

        from urllib.parse import urlencode
        keep = {"brand": brand}
        for k in ("country", "area", "region", "city", "group_company",
                  "subgroup_company", "pharmacy_category", "pharmacy_type",
                  "promo", "marketing_staff", "pharmacy_activeness", "pharmacy_address"):
            v = request.POST.get(k, "")
            if v:
                keep[k] = v
        return redirect(f"{request.path}?{urlencode(keep)}")

    filters = {k: request.GET.get(k, "").strip() for k in (
        "country", "area", "region", "city", "group_company", "subgroup_company",
        "pharmacy_category", "pharmacy_type", "promo", "marketing_staff",
        "pharmacy_activeness", "pharmacy_address",
    )}

    result = view_service.query(brand=brand, **filters)
    options = view_service.dropdown_options(
        brand=brand, country=filters["country"], area=filters["area"],
        region=filters["region"], city=filters["city"],
    )

    context = {
        "records": result["records"],
        "total_rows": result["total_rows"],
        "options": options,
        "brands": PHARMACY_BRANDS,
        "activeness_list": PHARMACY_ACTIVENESS,
        "brand": brand,
        "f": filters,
        "has_query": bool(request.GET),
    }
    return render(request, "sales/pharmacy_entry.html", context)

# ==== Sales Report Observation (Просмотр Сток и Продажа) — Phase 1 ====

REPORT_COMP_TYPES = [("SL", "SOLGAR"), ("OS", "OBF"), ("BN", "NATURES BOUNTY")]


@login_required
@require_screen("SALES_REPORT_OBS")
@require_http_methods(["GET"])
def sales_report_obs_view(request: HttpRequest) -> HttpResponse:
    """
    Sales Report Observation (Просмотр Сток и Продажа) - Phase 1.

    CHAIN_SALES report, monthly, with brand + date + chain + country filters.
    GET-driven: filters in the query string, report runs when dates are given.
    """
    from django.shortcuts import render

    from .services import ReportService

    service = ReportService()

    comp_type = (request.GET.get("comp_type") or "SL").strip()
    begin = (request.GET.get("begin") or "").strip()
    end = (request.GET.get("end") or "").strip()
    chain = (request.GET.get("chain") or "").strip()
    country = (request.GET.get("country") or "").strip()

    options = service.dropdown_options(comp_type)

    report = None
    error = ""
    if begin and end:
        # Tarih formatini normalize et: YYYY-MM-DD (input type=date) -> YYYYMMDD
        b = begin.replace("-", "")
        e = end.replace("-", "")
        if len(b) == 8 and len(e) == 8 and b.isdigit() and e.isdigit():
            try:
                report = service.run_chain_sales(comp_type, b, e, chain=chain, country=country)
            except Exception as exc:
                error = f"Ошибка отчета: {exc}"
        else:
            error = "Неверный формат даты."

    context = {
        "comp_types": REPORT_COMP_TYPES,
        "options": options,
        "report": report,
        "error": error,
        "f": {"comp_type": comp_type, "begin": begin, "end": end,
              "chain": chain, "country": country},
        "has_query": bool(request.GET),
    }
    return render(request, "sales/sales_report_obs.html", context)