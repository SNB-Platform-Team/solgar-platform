#1c api
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .views import OneCService


ONEC_API_TABS = [
    {"key": "orders", "label": "Заказы"},
    {"key": "shipments", "label": "Поставки"},
    {"key": "sales", "label": "Продажи"},
    {"key": "residues", "label": "Свободные остатки"},
]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onec_api(request):
    """
    1C stock data API (read-only). Returns a paginated, optionally filtered
    slice of one table (tab) as JSON for the React frontend.

    Query params:
      tab    - one of orders/shipments/sales/residues (default: orders)
      page   - 1-based page number (default: 1)
      search - product description / SAP filter (optional)

    Response:
      {
        tabs: [{key, label}, ...],
        tab, columns, rows, total_rows, page, num_pages, has_prev, has_next
      }
    """
    service = OneCService()

    valid = {t["key"] for t in ONEC_API_TABS}
    tab = (request.GET.get("tab") or "orders").strip().lower()
    if tab not in valid:
        tab = "orders"

    search = (request.GET.get("search") or "").strip()
    try:
        page = int(request.GET.get("page", "1"))
    except (TypeError, ValueError):
        page = 1

    try:
        result = service.get_table(tab, page=page, search=search)
    except Exception as exc:
        return Response({"error": f"Ошибка загрузки данных: {exc}"}, status=500)

    # rows tuple listesi -> JSON icin liste listesine cevir (zaten serializable
    # ama Decimal/date gibi tipler icin str guvenli). DRF cogunu halleder;
    # yine de tarih/decimal karisik olabilecegi icin satirlari normalize et.
    columns = result["columns"]
    raw_rows = result["rows"]
    rows = []
    for r in raw_rows:
        rows.append([_json_safe(v) for v in r])

    return Response({
        "tabs": ONEC_API_TABS,
        "tab": tab,
        "columns": columns,
        "rows": rows,
        "total_rows": result["total_rows"],
        "page": result["page"],
        "num_pages": result["num_pages"],
        "has_prev": result["has_prev"],
        "has_next": result["has_next"],
        "search": search,
    })


def _json_safe(value):
    """Convert DB values (Decimal, date, datetime) to JSON-friendly types."""
    import datetime
    from decimal import Decimal

    if value is None:
        return None
    if isinstance(value, Decimal):
        # tam sayiysa int, degilse float
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value



DOC_MGR_COMP_TYPES_API = [
    {"value": "", "label": "—"},
    {"value": "SOLGAR", "label": "SOLGAR"},
    {"value": "OBF", "label": "OBF"},
    {"value": "BOUNTY", "label": "NATURES BOUNTY"},
]
DOC_MGR_REP_TYPES_API = ["REGIONS", "MAIN_DISTRICT", "CITY", "MAIN_SPECIALITY",
                         "SUB_SPECIALITY", "MED_REPS", "CLINIC_NAME", "ACTIVATION_DATE"]
DOC_MGR_PARAMETERS_API = ["TOTAL_QUANTITY", "TOTAL_CATEGORY"]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctor_managerial_api(request):
    """
    Doctor Managerial report API. Returns dropdown options plus, when run=1,
    a grouped/counted report (columns + rows) as JSON for the React frontend.

    Query params (all optional):
      run        - "1" to actually run the report (otherwise only options)
      brand, rep_type, parameter
      country, region, city, speciality, sub_speciality, clinic, medrep,
      activeness, begin, end

    Response:
      {
        options: {comp_types, rep_types, parameters},
        report: {columns, rows, total_rows} | null,
        error: str,
        f: {...echoed filters...}
      }
    """
    from .views import DoctorManagerialService

    service = DoctorManagerialService()

    brand = (request.GET.get("brand") or "").strip()
    rep_type = (request.GET.get("rep_type") or "REGIONS").strip()
    parameter = (request.GET.get("parameter") or "TOTAL_QUANTITY").strip()
    country = (request.GET.get("country") or "").strip()
    region = (request.GET.get("region") or "").strip()
    city = (request.GET.get("city") or "").strip()
    speciality = (request.GET.get("speciality") or "").strip()
    sub_speciality = (request.GET.get("sub_speciality") or "").strip()
    clinic = (request.GET.get("clinic") or "").strip()
    medrep = (request.GET.get("medrep") or "").strip()
    activeness = (request.GET.get("activeness") or "").strip()
    begin = (request.GET.get("begin") or "").strip()
    end = (request.GET.get("end") or "").strip()

    report = None
    error = ""
    if request.GET.get("run"):
        try:
            result = service.run(
                brand=brand, rep_type=rep_type, parameter=parameter,
                country=country, region=region, city=city,
                speciality=speciality, sub_speciality=sub_speciality,
                clinic=clinic, medrep=medrep, activeness=activeness,
                begin=begin.replace("-", ""), end=end.replace("-", ""),
            )
            rows = [[_json_safe(v) for v in r] for r in result["rows"]]
            report = {
                "columns": result["columns"],
                "rows": rows,
                "total_rows": result.get("total_rows", len(rows)),
            }
        except Exception as exc:
            error = f"Ошибка отчета: {exc}"

    return Response({
        "options": {
            "comp_types": DOC_MGR_COMP_TYPES_API,
            "rep_types": DOC_MGR_REP_TYPES_API,
            "parameters": DOC_MGR_PARAMETERS_API,
        },
        "report": report,
        "error": error,
        "f": {
            "brand": brand, "rep_type": rep_type, "parameter": parameter,
            "country": country, "region": region, "city": city,
            "speciality": speciality, "sub_speciality": sub_speciality,
            "clinic": clinic, "medrep": medrep, "activeness": activeness,
            "begin": begin, "end": end,
        },
    })



PHARM_MGR_COMP_TYPES_API = [
    {"value": "SOLGAR", "label": "SOLGAR"},
    {"value": "OBF", "label": "OBF"},
    {"value": "BOUNTY", "label": "NATURES BOUNTY"},
]
PHARM_MGR_REP_TYPES_API = ["REGIONS", "MAIN_DISTRICT", "CITY", "MED_REPS",
                           "CHAINS", "ACTIVATION_DATE"]
PHARM_MGR_PARAMETERS_API = ["TOTAL_QUANTITY", "TOTAL_CATEGORY", "TOTAL_ACTIVENESS"]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pharm_managerial_api(request):
    """
    Pharmacy Managerial report API. Returns dropdown options plus, when run=1,
    a grouped/counted report (columns + rows) as JSON for the React frontend.

    Query params (all optional):
      run        - "1" to actually run the report (otherwise only options)
      brand, rep_type, parameter
      country, region, city, chain, medrep, activeness, begin, end

    Response:
      {
        options: {comp_types, rep_types, parameters},
        report: {columns, rows, total_rows} | null,
        error: str,
        f: {...echoed filters...}
      }
    """
    from .views import PharmManagerialService

    service = PharmManagerialService()

    brand = (request.GET.get("brand") or "SOLGAR").strip()
    rep_type = (request.GET.get("rep_type") or "REGIONS").strip()
    parameter = (request.GET.get("parameter") or "TOTAL_QUANTITY").strip()
    country = (request.GET.get("country") or "").strip()
    region = (request.GET.get("region") or "").strip()
    city = (request.GET.get("city") or "").strip()
    chain = (request.GET.get("chain") or "").strip()
    medrep = (request.GET.get("medrep") or "").strip()
    activeness = (request.GET.get("activeness") or "").strip()
    begin = (request.GET.get("begin") or "").strip()
    end = (request.GET.get("end") or "").strip()

    report = None
    error = ""
    if request.GET.get("run"):
        try:
            result = service.run(
                brand=brand, rep_type=rep_type, parameter=parameter,
                country=country, region=region, city=city, chain=chain,
                medrep=medrep, activeness=activeness,
                begin=begin.replace("-", ""), end=end.replace("-", ""),
            )
            rows = [[_json_safe(v) for v in r] for r in result["rows"]]
            report = {
                "columns": result["columns"],
                "rows": rows,
                "total_rows": result.get("total_rows", len(rows)),
            }
        except Exception as exc:
            error = f"Ошибка отчета: {exc}"

    return Response({
        "options": {
            "comp_types": PHARM_MGR_COMP_TYPES_API,
            "rep_types": PHARM_MGR_REP_TYPES_API,
            "parameters": PHARM_MGR_PARAMETERS_API,
        },
        "report": report,
        "error": error,
        "f": {
            "brand": brand, "rep_type": rep_type, "parameter": parameter,
            "country": country, "region": region, "city": city, "chain": chain,
            "medrep": medrep, "activeness": activeness,
            "begin": begin, "end": end,
        },
    })



# Tabloda gosterilecek kolonlar (entry ekranindaki ana alanlar).
# match_key bir @property (DB kolonu degil), o yuzden liste disinda.
_PHARMACY_API_COLUMNS = [
    ("pharmacy_no", "Номер аптеки"),
    ("group_company", "Сеть"),
    ("country", "Страна"),
    ("region", "Регион"),
    ("city", "Город"),
    ("pharmacy_address", "Адрес"),
    ("pharmacy_response_person", "Ответственный"),
    ("pharmacy_category", "Категория"),
    ("pharmacy_type", "Тип"),
]

PHARMACY_API_BRANDS = [
    {"value": "SOLGAR", "label": "SOLGAR"},
    {"value": "BOUNTY", "label": "NATURES BOUNTY"},
]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pharmacy_api(request):
    """
    Pharmacy entry list API (read-only, paginated, searchable).

    Query params:
      brand   - SOLGAR / BOUNTY (default SOLGAR)
      page    - 1-based page (default 1)
      search  - name / city / address filter (optional)

    Response:
      {
        brands, brand, columns, rows, total_rows,
        page, num_pages, has_prev, has_next, search
      }
    """
    from .services import PharmacyViewService

    service = PharmacyViewService()

    brand = (request.GET.get("brand") or "SOLGAR").strip()
    search = (request.GET.get("search") or "").strip()
    try:
        page = int(request.GET.get("page", "1"))
    except (TypeError, ValueError):
        page = 1

    fkeys = [
        "country", "area", "region", "city", "group_company",
        "subgroup_company", "pharmacy_category", "pharmacy_type", "promo",
        "marketing_staff", "pharmacy_activeness", "pharmacy_address",
    ]
    filters = {k: (request.GET.get(k) or "").strip() for k in fkeys}
    try:
        result = service.query(brand=brand, search=search, page=page, **filters)
    except Exception as exc:
        return Response({"error": f"Ошибка загрузки: {exc}"}, status=500)

    # Model instance'larini satir listesine cevir (secili kolonlar)
    col_keys = [c[0] for c in _PHARMACY_API_COLUMNS]
    col_labels = [c[1] for c in _PHARMACY_API_COLUMNS]
    rows = []
    for rec in result["records"]:
        rows.append([_json_safe(getattr(rec, k, "")) for k in col_keys])

    return Response({
        "brands": PHARMACY_API_BRANDS,
        "brand": brand,
        "columns": col_labels,
        "rows": rows,
        "total_rows": result["total_rows"],
        "page": result["page"],
        "num_pages": result["num_pages"],
        "has_prev": result["has_prev"],
        "has_next": result["has_next"],
        "search": search,
        "filters": filters,
    })



# Tabloda gosterilecek kolonlar (doctor entry ana alanlari).
_DOCTOR_API_COLUMNS = [
    ("doctor_name", "ФИО врача"),
    ("country", "Страна"),
    ("region", "Регион"),
    ("city", "Город"),
    ("specialty", "Специальность"),
    ("clinic_name", "Клиника"),
    ("medrep", "Мед. представитель"),
    ("category", "Категория"),
]

# doctor_data'da brand tam isim olarak saklanir (SOLGAR / NATURES BOUNTY).
DOCTOR_API_BRANDS = [
    {"value": "", "label": "Все"},
    {"value": "SOLGAR", "label": "SOLGAR"},
    {"value": "NATURES BOUNTY", "label": "NATURES BOUNTY"},
]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctor_api(request):
    """
    Doctor entry list API (read-only, paginated, searchable).

    Query params:
      brand   - "" (all) / SOLGAR / "NATURES BOUNTY"
      page    - 1-based page (default 1)
      search  - name / city / clinic filter (optional)

    Response:
      {
        brands, brand, columns, rows, total_rows,
        page, num_pages, has_prev, has_next, search
      }
    """
    from .services import DoctorViewService

    service = DoctorViewService()

    brand = (request.GET.get("brand") or "").strip()
    search = (request.GET.get("search") or "").strip()
    try:
        page = int(request.GET.get("page", "1"))
    except (TypeError, ValueError):
        page = 1

    try:
        result = service.query(brand=brand, search=search, page=page)
    except Exception as exc:
        return Response({"error": f"Ошибка загрузки: {exc}"}, status=500)

    col_keys = [c[0] for c in _DOCTOR_API_COLUMNS]
    col_labels = [c[1] for c in _DOCTOR_API_COLUMNS]
    rows = []
    for rec in result["records"]:
        rows.append([_json_safe(getattr(rec, k, "")) for k in col_keys])

    return Response({
        "brands": DOCTOR_API_BRANDS,
        "brand": brand,
        "columns": col_labels,
        "rows": rows,
        "total_rows": result["total_rows"],
        "page": result["page"],
        "num_pages": result["num_pages"],
        "has_prev": result["has_prev"],
        "has_next": result["has_next"],
        "search": search,
    })



import datetime as _dt

CHAIN_REPORT_BRANDS_API = [
    {"value": "", "label": "Все"},
    {"value": "SL", "label": "SOLGAR"},
    {"value": "BN", "label": "NATURES BOUNTY"},
#   {"value": "OFB", "label": "OTHERS"},     
    ]

_CHAIN_REPORT_PAGE_SIZE = 200


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chain_report_api(request):
    """
    Chain sales report API (Аптечная сеть продаж). Date-range chain sales with
    brand totals, paginated table.

    Query params (all optional):
      brand, chain_name, country, city, date_from, date_to, search (q)
      main_group, sub_group, region, district
      page

    Response:
      {
        brands, columns, rows, total_rows, page, num_pages, has_prev, has_next,
        totals: {solgar_count, solgar_amount, bounty_count, bounty_amount},
        f: {...echoed filters...}
      }
    """
    from .services import SalesViewService

    service = SalesViewService()

    filters = {}
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()
    if date_from:
        try:
            filters["date_from"] = _dt.datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            pass
    if date_to:
        try:
            filters["date_to"] = _dt.datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            pass
    for key in ("chain_name", "country", "brand", "city"):
        val = (request.GET.get(key) or "").strip()
        if val:
            filters[key] = val
    search = (request.GET.get("q") or request.GET.get("search") or "").strip()
    if search:
        filters["search"] = search

    main_group = (request.GET.get("main_group") or "").strip()
    sub_group = (request.GET.get("sub_group") or "").strip()
    region = (request.GET.get("region") or "").strip()
    district = (request.GET.get("district") or "").strip()

    try:
        page = int(request.GET.get("page", "1"))
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1

    try:
        result = service.chain_report(
            main_group=main_group, sub_group=sub_group,
            region=region, district=district, **filters
        )
    except Exception as exc:
        return Response({"error": f"Ошибка отчета: {exc}"}, status=500)

    qs = result["records"]
    total = result["total_rows"]

    size = _CHAIN_REPORT_PAGE_SIZE
    start = (page - 1) * size
    page_records = list(qs[start:start + size])
    num_pages = max(1, (total + size - 1) // size)

    columns = ["Компания", "Наименование", "Сеть", "Дата", "Город",
               "Аптека", "Кол-во", "Сумма"]
    rows = []
    for rec in page_records:
        rows.append([
            rec.get_brand_display() if hasattr(rec, "get_brand_display") else _json_safe(getattr(rec, "brand", "")),
            _json_safe(getattr(rec, "product_name", "")),
            _json_safe(getattr(rec, "chain_name", "")),
            rec.report_date.strftime("%d.%m.%Y") if getattr(rec, "report_date", None) else "",
            _json_safe(getattr(rec, "city", "") or ""),
            _json_safe(getattr(rec, "pharmacy", "") or ""),
            _json_safe(getattr(rec, "count", 0)),
            _json_safe(getattr(rec, "amount", 0)),
        ])

    return Response({
        "brands": CHAIN_REPORT_BRANDS_API,
        "columns": columns,
        "rows": rows,
        "total_rows": total,
        "page": page,
        "num_pages": num_pages,
        "has_prev": page > 1,
        "has_next": page < num_pages,
        "totals": {
            "solgar_count": _json_safe(result.get("solgar_count", 0)),
            "solgar_amount": _json_safe(result.get("solgar_amount", 0)),
            "bounty_count": _json_safe(result.get("bounty_count", 0)),
            "bounty_amount": _json_safe(result.get("bounty_amount", 0)),
        },
        "f": {
            "brand": request.GET.get("brand", ""), "chain_name": request.GET.get("chain_name", ""),
            "country": request.GET.get("country", ""), "city": request.GET.get("city", ""),
            "date_from": date_from, "date_to": date_to, "search": search,
        },
    })



SALES_OBS_COMP_TYPES_API = [
    {"value": "SL", "label": "SOLGAR"},
    {"value": "OS", "label": "OBF"},
    {"value": "BN", "label": "NATURES BOUNTY"},
]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_obs_api(request):
    """
    Sales Report Observation API (Просмотр Сток и Продажа). Monthly CHAIN_SALES
    pivot report. Returns filter options plus, when a valid date range is given,
    the pivot (columns + rows).

    Query params:
      comp_type  - SL / OS / BN (default SL)
      begin, end - YYYY-MM-DD (both required to run)
      chain, country - optional filters

    Response:
      {
        comp_types, options: {chains, countries},
        report: {columns, rows, total_rows} | null,
        error, f
      }
    """
    from .services import ReportService

    service = ReportService()

    comp_type = (request.GET.get("comp_type") or "SL").strip()
    begin = (request.GET.get("begin") or "").strip()
    end = (request.GET.get("end") or "").strip()
    chain = (request.GET.get("chain") or "").strip()
    country = (request.GET.get("country") or "").strip()
    area = (request.GET.get("area") or "").strip()
    region = (request.GET.get("region") or "").strip()
    city = (request.GET.get("city") or "").strip()
    medrep = (request.GET.get("medrep") or "").strip()

    try:
        options = service.dropdown_options(comp_type)
    except Exception:
        options = {"chains": [], "countries": []}

    report = None
    error = ""
    if begin and end:
        b = begin.replace("-", "")
        e = end.replace("-", "")
        if len(b) == 8 and len(e) == 8 and b.isdigit() and e.isdigit():
            try:
                result = service.run_chain_sales(
                    comp_type, b, e, chain=chain, country=country,
                    area=area, region=region, city=city, medrep=medrep,
                )
                rows = [[_json_safe(v) for v in r] for r in result["rows"]]
                report = {
                    "columns": result["columns"],
                    "rows": rows,
                    "total_rows": result.get("total_rows", len(rows)),
                }
            except Exception as exc:
                error = f"Ошибка отчета: {exc}"
        else:
            error = "Неверный формат даты."

    return Response({
        "comp_types": SALES_OBS_COMP_TYPES_API,
        "options": {
            "chains": list(options.get("chains", [])),
            "countries": list(options.get("countries", [])),
        },
        "report": report,
        "error": error,
        "f": {"comp_type": comp_type, "begin": begin, "end": end,
              "chain": chain, "country": country, "area": area,
              "region": region, "city": city, "medrep": medrep},
    })


# ==================== Sales Obs Filter Options API (cascading geo) ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_obs_filter_options_api(request):
    """
    Cascading geographic dropdown for the Sales Report Observation screen.
    Country -> Area -> Region -> City, each level narrowed by parents.

    Query params: level (area/region/city), country, area, region
    """
    from .services import ReportService

    level = (request.GET.get("level") or "").strip()
    country = (request.GET.get("country") or "").strip()
    area = (request.GET.get("area") or "").strip()
    region = (request.GET.get("region") or "").strip()

    try:
        options = ReportService().cascade_options(
            level, country=country, area=area, region=region
        )
    except Exception:
        options = []

    return Response({"level": level, "options": list(options)})



import datetime as _dt_dash
from django.core.cache import cache as _dash_cache


def _dash_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """
    Dashboard summary API: headline counters, top chains, monthly sales trend.
    Cached 10 minutes.
    """
    from .services import ReportService, PharmacyViewService, DoctorViewService

    cached = _dash_cache.get("dashboard_summary_v1")
    if cached is not None:
        return Response(cached)

    year = _dt_dash.date.today().year
    begin = f"{year}0101"
    end = f"{year}1231"
    comp_type = "SL"

    report = None
    try:
        service = ReportService()
        report = service.run_chain_sales(comp_type, begin, end, chain="", country="")
    except Exception:
        report = None

    top_chains = []
    monthly = []
    sales_total = 0

    if report and report.get("rows"):
        columns = report["columns"]
        rows = report["rows"]
        try:
            chain_idx = columns.index("chain")
        except ValueError:
            chain_idx = 1
        try:
            total_idx = columns.index("Total")
        except ValueError:
            total_idx = len(columns) - 1

        month_cols = [(i, c) for i, c in enumerate(columns)
                      if "_" in c and c.split("_")[0].isdigit()]

        chain_totals = []
        for r in rows:
            name = str(r[chain_idx])
            total = _dash_int(r[total_idx])
            chain_totals.append((name, total))
            sales_total += total
        chain_totals.sort(key=lambda x: x[1], reverse=True)
        top_chains = [{"name": n, "total": t} for n, t in chain_totals[:10]]

        _MONTH_RU = {
            "Jan": "Янв", "Feb": "Фев", "Mar": "Мар", "Apr": "Апр",
            "May": "Май", "Jun": "Июн", "Jul": "Июл", "Aug": "Авг",
            "Sep": "Сен", "Oct": "Окт", "Nov": "Ноя", "Dec": "Дек",
        }
        for i, cname in month_cols:
            msum = sum(_dash_int(r[i]) for r in rows)
            label = cname.split("_")[-1]
            monthly.append({"month": _MONTH_RU.get(label, label), "total": msum})

    pharmacies = 0
    doctors = 0
    try:
        pv = PharmacyViewService()
        res_s = pv.query(brand="SOLGAR", search="", page=1)
        res_b = pv.query(brand="BOUNTY", search="", page=1)
        pharmacies = _dash_int(res_s.get("total_rows", 0)) + _dash_int(res_b.get("total_rows", 0))
    except Exception:
        pharmacies = 0
    try:
        dv = DoctorViewService()
        res_d = dv.query(brand="", search="", page=1)
        doctors = _dash_int(res_d.get("total_rows", 0))
    except Exception:
        doctors = 0

    chains_count = len(report["rows"]) if (report and report.get("rows")) else 0

    payload = {
        "cards": {
            "pharmacies": pharmacies,
            "doctors": doctors,
            "chains": chains_count,
            "sales_total": sales_total,
        },
        "top_chains": top_chains,
        "monthly": monthly,
        "period": {"begin": begin, "end": end, "comp_type": comp_type},
    }

    _dash_cache.set("dashboard_summary_v1", payload, 600)
    return Response(payload)


#faq
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def faq_api(request):
    """Rule-based FAQ: user's accessible screens + static Q/A."""
    from authorization.models import Screen
    from authorization.context_processors import accessible_screens as _acc

    codes = _acc(request).get("accessible_screens", set())
    name_by_code = dict(Screen.objects.values_list("code", "name"))
    my_screens = sorted({name_by_code.get(c, c) for c in codes if c in name_by_code})

    faq = [
        {"q": "Что это за платформа?",
         "a": ("Внутренняя платформа Solgar — веб-версия системы Solgar Intern. "
               "Она объединяет отчёты по продажам, справочники аптек и врачей, "
               "данные 1С-склада и аналитику в одном месте.")},
        {"q": "Какие разделы мне доступны?",
         "a": ("Ниже перечислены экраны, к которым у вас есть доступ. "
               "Если нужного раздела нет в списке, обратитесь к администратору.")},
        {"q": "Откуда берутся данные?",
         "a": ("Справочные данные (аптеки, врачи, регионы) поступают из внешней "
               "базы; данные о продажах загружаются из Excel-файлов; складские "
               "остатки и заказы — напрямую из 1С.")},
        {"q": "Как сформировать отчёт?",
         "a": ("Откройте нужный экран отчёта, выберите фильтры (компания, период, "
               "регион и т.д.) и нажмите «Сформировать отчёт». Результат появится "
               "в виде таблицы.")},
        {"q": "К кому обращаться за помощью?",
         "a": ("По вопросам доступа и работы платформы обращайтесь к вашему "
               "администратору или в отдел ИТ.")},
    ]

    return Response({
        "user_display": request.user.get_full_name() or request.user.username,
        "my_screens": my_screens,
        "faq": faq,
    })



from django.http import JsonResponse as _CsrfJsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie as _ensure_csrf_cookie
from django.contrib.auth.decorators import login_required as _csrf_login_required


@_ensure_csrf_cookie
@_csrf_login_required
def csrf_api(request):
    """Sets the csrftoken cookie so React can send X-CSRFToken on POSTs."""
    from django.middleware.csrf import get_token
    return _CsrfJsonResponse({"csrfToken": get_token(request)})



from decimal import Decimal as _UL_Decimal
from datetime import datetime as _ul_datetime


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_upload_options_api(request):
    """Dropdown options for the sales upload screen: active chains + countries."""
    from .models import ChainDefinition
    try:
        from .views import COUNTRIES
    except Exception:
        COUNTRIES = []
    chains = list(
        ChainDefinition.objects.filter(is_active=True).values_list("name", flat=True)
    )
    return Response({"chains": sorted(chains), "countries": list(COUNTRIES)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sales_upload_preview_api(request):
    """Parse an uploaded chain sales Excel file and return parsed rows (stateless)."""
    from .models import ChainDefinition
    from .services import SalesUploadService, SalesParseError

    report_date = (request.POST.get("report_date") or "").strip()
    chain_name = (request.POST.get("chain_name") or "").strip()
    country = (request.POST.get("country") or "").strip()
    excel_file = request.FILES.get("excel_file")

    if not excel_file:
        return Response({"error": "Выберите файл Excel."}, status=400)
    if not report_date or not chain_name or not country:
        return Response({"error": "Заполните дату, сеть и страну."}, status=400)
    try:
        _ul_datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Неверный формат даты (ГГГГ-ММ-ДД)."}, status=400)

    try:
        definition = ChainDefinition.objects.get(name=chain_name, is_active=True)
    except ChainDefinition.DoesNotExist:
        return Response({"error": f"Определение для сети «{chain_name}» не найдено."}, status=400)

    service = SalesUploadService()
    try:
        result = service.preview(excel_file, definition, excel_file.name)
    except SalesParseError as exc:
        return Response({"error": str(exc)}, status=400)

    if result.total_rows == 0:
        return Response({"error": "В файле не найдено ни одной строки с данными."}, status=400)

    rows = []
    for r in result.rows:
        rows.append({
            "product_name": r.product_name, "brand": r.brand,
            "pharmacy": r.pharmacy, "city": r.city,
            "count": _json_safe(r.count), "amount": _json_safe(r.amount),
            "remaining_count": _json_safe(r.remaining_count),
            "remaining_amount": _json_safe(r.remaining_amount),
        })

    solgar_remaining = sum(
        r.remaining_amount for r in result.rows if r.brand == "SOLGAR"
    )
    bounty_remaining = sum(
        r.remaining_amount for r in result.rows if r.brand != "SOLGAR"
    )

    return Response({
        "rows": rows,
        "total_rows": result.total_rows,
        "summary": {
            "solgar_count": _json_safe(result.solgar_count),
            "solgar_amount": _json_safe(result.solgar_amount),
            "bounty_count": _json_safe(result.bounty_count),
            "bounty_amount": _json_safe(result.bounty_amount),
            "solgar_remaining": _json_safe(solgar_remaining),
            "bounty_remaining": _json_safe(bounty_remaining),
            "product_types": _json_safe(result.product_types),
        },
        "meta": {"report_date": report_date, "chain_name": chain_name, "country": country},
        "error": "",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sales_upload_save_api(request):
    """Save previously previewed sales rows sent back by the frontend."""
    from .services import SalesUploadService, ParsedRow, ParseResult

    data = request.data or {}
    rows_in = data.get("rows") or []
    report_date_str = (data.get("report_date") or "").strip()
    chain_name = (data.get("chain_name") or "").strip()
    country = (data.get("country") or "").strip()

    if not rows_in:
        return Response({"error": "Нет строк для сохранения."}, status=400)
    if not report_date_str or not chain_name or not country:
        return Response({"error": "Отсутствуют дата, сеть или страна."}, status=400)

    try:
        report_date = _ul_datetime.strptime(report_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Неверный формат даты."}, status=400)

    try:
        rows = [
            ParsedRow(
                product_name=r["product_name"], brand=r["brand"],
                pharmacy=r["pharmacy"], city=r["city"],
                count=int(r["count"]), amount=_UL_Decimal(str(r["amount"])),
                remaining_count=int(r["remaining_count"]),
                remaining_amount=_UL_Decimal(str(r["remaining_amount"])),
            )
            for r in rows_in
        ]
    except (KeyError, ValueError, TypeError) as exc:
        return Response({"error": f"Некорректные данные строк: {exc}"}, status=400)

    result = ParseResult(rows=rows)
    service = SalesUploadService()
    try:
        created = service.save_records(result, report_date, chain_name, country, request.user)
    except Exception as exc:
        return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)

    return Response({"created": created, "error": ""})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def distributor_upload_options_api(request):
    """Dropdown options: active distributors, countries, operation types."""
    from .models import ChainDefinition, DistributorRecord
    try:
        from .views import COUNTRIES
    except Exception:
        COUNTRIES = []
    distributors = list(
        ChainDefinition.objects.filter(
            is_active=True, source_type=ChainDefinition.SourceType.DISTRIBUTOR
        ).values_list("name", flat=True)
    )
    operations = [{"value": v, "label": l} for v, l in DistributorRecord.Operation.choices]
    return Response({
        "distributors": sorted(distributors),
        "countries": list(COUNTRIES),
        "operations": operations,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def distributor_upload_preview_api(request):
    """Parse a distributor Excel file, return parsed rows as JSON (stateless)."""
    from .models import ChainDefinition
    from .services import DistributorUploadService, SalesParseError

    distributor = (request.POST.get("distributor") or "").strip()
    operation_type = (request.POST.get("operation_type") or "").strip()
    country = (request.POST.get("country") or "").strip()
    begin_date = (request.POST.get("begin_date") or "").strip()
    end_date = (request.POST.get("end_date") or "").strip()
    excel_file = request.FILES.get("excel_file")

    if not excel_file:
        return Response({"error": "Выберите файл Excel."}, status=400)
    if not distributor or not operation_type or not country:
        return Response({"error": "Заполните дистрибьютора, тип операции и страну."}, status=400)

    try:
        definition = ChainDefinition.objects.get(
            name=distributor, is_active=True,
            source_type=ChainDefinition.SourceType.DISTRIBUTOR,
        )
    except ChainDefinition.DoesNotExist:
        return Response({"error": f"Определение для «{distributor}» не найдено."}, status=400)

    try:
        result = DistributorUploadService().preview(excel_file, definition, excel_file.name)
    except SalesParseError as exc:
        return Response({"error": str(exc)}, status=400)

    if result.total_rows == 0:
        return Response({"error": "В файле не найдено ни одной строки с данными."}, status=400)

    rows = []
    for r in result.rows:
        rows.append({
            "product_name": r.product_name, "brand": r.brand,
            "client": r.pharmacy, "city": r.city,
            "count": _json_safe(r.count), "amount": _json_safe(r.amount),
        })

    return Response({
        "rows": rows, "total_rows": result.total_rows,
        "meta": {"distributor": distributor, "operation_type": operation_type,
                 "country": country, "begin_date": begin_date, "end_date": end_date},
        "error": "",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def distributor_upload_save_api(request):
    """Save previously previewed distributor rows."""
    from .services import DistributorUploadService, ParsedRow, ParseResult
    from decimal import Decimal as _DL_Decimal
    from datetime import datetime as _dl_datetime

    data = request.data or {}
    rows_in = data.get("rows") or []
    distributor = (data.get("distributor") or "").strip()
    operation_type = (data.get("operation_type") or "").strip()
    country = (data.get("country") or "").strip()
    begin_date_str = (data.get("begin_date") or "").strip()
    end_date_str = (data.get("end_date") or "").strip()

    if not rows_in:
        return Response({"error": "Нет строк для сохранения."}, status=400)
    if not distributor or not operation_type or not country:
        return Response({"error": "Отсутствуют дистрибьютор, тип операции или страна."}, status=400)

    begin_date = None
    end_date = None
    try:
        if begin_date_str:
            begin_date = _dl_datetime.strptime(begin_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = _dl_datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Неверный формат даты."}, status=400)

    try:
        rows = [
            ParsedRow(
                product_name=r["product_name"], brand=r["brand"],
                pharmacy=r["client"], city=r["city"],
                count=int(r["count"]), amount=_DL_Decimal(str(r["amount"])),
                remaining_count=0, remaining_amount=_DL_Decimal("0"),
            )
            for r in rows_in
        ]
    except (KeyError, ValueError, TypeError) as exc:
        return Response({"error": f"Некорректные данные строк: {exc}"}, status=400)

    result = ParseResult(rows=rows)
    try:
        created = DistributorUploadService().save_records(
            result, distributor, operation_type, country, begin_date, end_date, request.user
        )
    except Exception as exc:
        return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)

    return Response({"created": created, "error": ""})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pharmacy_filter_options_api(request):
    """
    Dropdown data for the Pharmacy screen filters. Brand-scoped.

    Two modes:
      1) No `level` param: returns ALL top-level lists at once (initial load) --
         countries, chains, categories, types, promos, marketing_staff.
      2) With `level` param: returns ONE cascading list based on parent values
         (level=area/region/city/metro/subchain), mirroring the Java AJAX
         cascade. Used when the user picks a parent value.

    Query params:
      brand (SOLGAR/BOUNTY), level, country, area, region, city, group_company
    """
    from .repositories import PharmacyRepository

    repo = PharmacyRepository()
    brand = (request.GET.get("brand") or "SOLGAR").strip()
    level = (request.GET.get("level") or "").strip()
    country = (request.GET.get("country") or "").strip()
    area = (request.GET.get("area") or "").strip()
    region = (request.GET.get("region") or "").strip()
    city = (request.GET.get("city") or "").strip()
    group_company = (request.GET.get("group_company") or "").strip()

    if level:
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
        return Response({"level": level, "options": list(options)})

    def _safe(fn, *a, **kw):
        try:
            return list(fn(*a, **kw))
        except Exception:
            return []

    return Response({
        "countries": _safe(repo.countries, brand),
        "chains": _safe(repo.chains, brand),
        "categories": _safe(repo.pharmacy_categories, brand),
        "types": _safe(repo.pharmacy_types, brand),
        "promos": _safe(repo.promos, brand),
        "marketing_staff": _safe(repo.marketing_staff, brand),
    })





# ==================== Doctor Filter Options API (cascading dropdowns) ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctor_filter_options_api(request):
    """
    Dropdown data for the Doctor screen filters.

    Two modes:
      1) No `level`: all top-level lists (countries, specialties,
         unified_specialties, medreps).
      2) With `level` (area/region/city): one cascading list narrowed by
         parent selections (country -> area -> region -> city).

    Query params: level, country, area, region
    """
    from .repositories import DoctorRepository

    repo = DoctorRepository()
    level = (request.GET.get("level") or "").strip()
    country = (request.GET.get("country") or "").strip()
    area = (request.GET.get("area") or "").strip()
    region = (request.GET.get("region") or "").strip()

    if level:
        if level == "area":
            options = repo.areas(country=country)
        elif level == "region":
            options = repo.regions(country=country, area=area)
        elif level == "city":
            options = repo.cities(country=country, area=area, region=region)
        else:
            options = []
        return Response({"level": level, "options": list(options)})

    def _safe(fn, *a, **kw):
        try:
            return list(fn(*a, **kw))
        except Exception:
            return []

    return Response({
        "countries": _safe(repo.countries),
        "specialties": _safe(repo.specialties),
        "unified_specialties": _safe(repo.unified_specialties),
        "medreps": _safe(repo.medreps),
    })


# ==================== Current user (auth check) API ====================

from rest_framework.permissions import AllowAny as _AllowAny


@api_view(["GET"])
@permission_classes([_AllowAny])
def me_api(request):
    """
    Returns the current user's auth state. React calls this on load to decide
    whether to show the app or redirect to login. AllowAny so it can be called
    while logged out (returns authenticated: false instead of 403).
    """
    if request.user and request.user.is_authenticated:
        return Response({
            "authenticated": True,
            "username": request.user.username,
            "display_name": request.user.get_full_name() or request.user.username,
            "is_staff": request.user.is_staff,
        })
    return Response({"authenticated": False})


# ==================== Chain Report Filter Options API (cascading) ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chain_report_filter_options_api(request):
    """
    Dropdown data for the Chain Report (Аптечная сеть продаж) filters.

    Mirrors the Java country -> dependent cascade: when a country is chosen,
    the chains / regions / districts lists narrow to that country. Called with
    ?country=... to refresh dependents, or without for the full initial set.

    Query params: country (optional)

    Response: {countries, chains, regions, districts}
    """
    from .services import SalesViewService
    try:
        from .views import COUNTRIES
    except Exception:
        COUNTRIES = []

    country = (request.GET.get("country") or "").strip()
    service = SalesViewService()

    try:
        options = service.filter_options(country=country)
    except Exception:
        options = {}

    return Response({
        "countries": list(COUNTRIES),
        "chains": list(options.get("chains", [])),
        "regions": list(options.get("regions", [])),
        "districts": list(options.get("districts", [])),
    })
