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
    main_group = (request.GET.get("main_group") or "").strip()
    sub_group = (request.GET.get("sub_group") or "").strip()
    product_name = (request.GET.get("product_name") or "").strip()

    try:
        options = service.dropdown_options(comp_type)
    except Exception:
        options = {"chains": [], "countries": [], "main_groups": [], "sub_groups": []}

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
                    main_group=main_group, sub_group=sub_group,
                    product_name=product_name,
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
            "main_groups": list(options.get("main_groups", [])),
            "sub_groups": list(options.get("sub_groups", [])),
        },
        "report": report,
        "error": error,
        "f": {"comp_type": comp_type, "begin": begin, "end": end,
              "chain": chain, "country": country, "area": area,
              "region": region, "city": city, "medrep": medrep,
              "main_group": main_group, "sub_group": sub_group,
              "product_name": product_name},
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

    # Ürün kademesi: level=product_name, main_group + sub_group parametreleriyle.
    if level == "product_name":
        main_group = (request.GET.get("main_group") or "").strip()
        sub_group = (request.GET.get("sub_group") or "").strip()
        # Grup secilmeden TUM urunleri dondurmek cok agir (binlerce) ve
        # tarayiciyi kilitler. En az bir grup filtresi sart.
        if not main_group and not sub_group:
            return Response({"level": level, "options": []})
        try:
            options = ReportService().product_names(main_group, sub_group)
        except Exception:
            options = []
        return Response({"level": level, "options": list(options[:500])})

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
            "country": getattr(request.user, "country", "") or "",
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


# ==================== User Profile API (view + update) ====================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def profile_api(request):
    """
    Current user's profile. GET returns the editable + read-only fields;
    POST updates the editable ones (first_name, last_name, email, phone,
    department). Username, user_type and access level are read-only.

    For Azure (SSO) users, edits here only affect the local Django record;
    the frontend shows a note that Azure-managed fields may be overwritten
    on next sign-in.
    """
    user = request.user

    if request.method == "POST":
        data = request.data or {}
        # Only these fields are editable; everything else is ignored.
        for field in ("first_name", "last_name", "email", "phone", "department"):
            if field in data:
                setattr(user, field, (data.get(field) or "").strip())
        try:
            user.save(update_fields=[
                "first_name", "last_name", "email", "phone", "department",
            ])
        except Exception as exc:
            return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)

    access_level = ""
    try:
        if getattr(user, "access_level", None):
            access_level = str(user.access_level)
    except Exception:
        access_level = ""

    return Response({
        "username": user.username,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "email": user.email or "",
        "phone": getattr(user, "phone", "") or "",
        "department": getattr(user, "department", "") or "",
        "user_type": getattr(user, "user_type", "") or "",
        "is_azure": getattr(user, "user_type", "") == "AZURE",
        "access_level": access_level,
        "is_staff": user.is_staff,
        "display_name": user.get_full_name() or user.username,
    })


# ==================== Employees / Users list API ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def employees_api(request):
    """
    Staff (User) list for the Сотрудники screen. Paginated + searchable.
    Read-only: shows name, email, phone, department, status, role.

    Query params: search, page
    """
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator
    from django.db.models import Q

    User = get_user_model()

    search = (request.GET.get("search") or "").strip()
    try:
        page = int(request.GET.get("page", "1"))
    except (TypeError, ValueError):
        page = 1

    qs = User.objects.all().order_by("username")
    if search:
        qs = qs.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(department__icontains=search)
        )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(page)

    rows = []
    for u in page_obj.object_list:
        # Status: enabled/disabled + account type
        if not getattr(u, "is_enabled", True):
            status = "disabled"
            status_label = "Отключён"
        elif getattr(u, "user_type", "") == "AZURE":
            status = "azure"
            status_label = "Azure"
        else:
            status = "active"
            status_label = "Активен"

        # Role: access level name, or staff/user
        role = ""
        try:
            if getattr(u, "access_level", None):
                role = str(u.access_level)
        except Exception:
            role = ""
        if not role:
            role = "Администратор" if u.is_staff else "Пользователь"

        rows.append({
            "username": u.username,
            "name": u.get_full_name() or u.username,
            "email": u.email or "",
            "phone": getattr(u, "phone", "") or "",
            "department": getattr(u, "department", "") or "",
            "status": status,
            "status_label": status_label,
            "role": role,
        })

    return Response({
        "rows": rows,
        "total_rows": paginator.count,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "has_prev": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "search": search,
    })


# ==================== Country options API (user-scoped) ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def country_options_api(request):
    """
    Country dropdown options from solgar_prm.prm_countries, scoped to the
    current user:
      - Staff/admin: all active countries, dropdown editable.
      - Regular user with a country set: only that country, dropdown LOCKED.

    Response:
      {
        countries: [str, ...],     # allowed countries for this user
        locked: bool,              # true => user must not change (single country)
        user_country: str,         # the user's own country ("" for admin)
        is_staff: bool,
      }
    """
    from django.db import connections

    user = request.user
    is_staff = bool(user.is_staff)
    user_country = (getattr(user, "country", "") or "").strip()

    # Full active country list from prm_countries.
    all_countries = []
    try:
        with connections["refdb"].cursor() as cur:
            cur.execute(
                "SELECT country FROM solgar_prm.prm_countries "
                "WHERE status = 1 ORDER BY country"
            )
            all_countries = [r[0] for r in cur.fetchall()]
    except Exception:
        all_countries = []

    # Admin/staff -> all countries, not locked.
    if is_staff or not user_country:
        return Response({
            "countries": all_countries,
            "locked": False,
            "user_country": user_country,
            "is_staff": is_staff,
        })

    # Regular user with a country -> only that country, locked.
    allowed = [c for c in all_countries if c == user_country] or [user_country]
    return Response({
        "countries": allowed,
        "locked": True,
        "user_country": user_country,
        "is_staff": is_staff,
    })


# ==================== Storage options API (distributor, country-scoped) ====================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def storage_options_api(request):
    """
    Distributor storage (склад) options from solgar_prm.prm_storages,
    filtered by country. If the user is country-restricted (non-staff with a
    country set), the country is forced to the user's own regardless of the
    query param.

    Query params: country (optional; ignored/overridden for restricted users)

    Response: {storages: [str, ...], country: str}
    """
    from django.db import connections

    user = request.user
    requested = (request.GET.get("country") or "").strip()
    user_country = (getattr(user, "country", "") or "").strip()

    # Country-restricted user: force their own country.
    if not user.is_staff and user_country:
        country = user_country
    else:
        country = requested

    storages = []
    try:
        with connections["refdb"].cursor() as cur:
            if country:
                cur.execute(
                    "SELECT storage FROM solgar_prm.prm_storages "
                    "WHERE country = %s ORDER BY storage",
                    [country],
                )
            else:
                cur.execute(
                    "SELECT DISTINCT storage FROM solgar_prm.prm_storages "
                    "ORDER BY storage"
                )
            storages = [r[0] for r in cur.fetchall()]
    except Exception:
        storages = []

    return Response({"storages": storages, "country": country})


# ==================== Depo (parametrik parser) upload API ====================
# Yeni parametrik parser (DepoStorageParser + config) tabanli distributor
# upload. Java StorageSalesStockUpload'in Python karsiligi.

# ==================== Depo (parametrik parser) upload API - batch/taslak ====================
# Preview: parse -> DistributorRecord'a batch_id + is_confirmed=False (taslak) yaz.
# Page: batch'ten sayfa sayfa oku (DB pagination). Save: batch'i onayla.

import uuid as _uuid


def _open_sheet(excel_file):
    """Yuklenen Excel'i oku (xlsx: openpyxl, xls: xlrd). (sheet, err) doner."""
    import io
    data = excel_file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        return wb.active, None
    except Exception:
        pass
    try:
        import xlrd
        book = xlrd.open_workbook(file_contents=data)
        s = book.sheet_by_index(0)

        class _C:
            def __init__(self, v): self.value = v

        class _W:
            def __init__(self, sh):
                self._s = sh
                self.max_row = sh.nrows
                self.max_column = sh.ncols
            def cell(self, row, column):
                r, c = row - 1, column - 1
                if 0 <= r < self._s.nrows and 0 <= c < self._s.ncols:
                    return _C(self._s.cell_value(r, c))
                return _C(None)

        return _W(s), None
    except Exception as exc:
        return None, f"Excel okunamadi: {exc}"


def _depo_row_to_record(r, batch_id, distributor, country, op_code, begin_date, end_date, user):
    """Parse satirini (dict) DistributorRecord taslagina cevir."""
    from .models import DistributorRecord
    from decimal import Decimal as _Dec

    pt = (r.get("product_type") or "").upper()
    brand = "BOUNTY" if pt == "BN" else ("OS" if pt == "OS" else "SOLGAR")
    return DistributorRecord(
        distributor=distributor,
        operation_type=op_code,
        country=country,
        begin_date=begin_date,
        end_date=end_date,
        product_name=(r.get("product") or "")[:300],
        product_type=(r.get("product_type") or "")[:120],
        brand=brand,
        count=int(r.get("count") or 0),
        amount=_Dec(str(r.get("amount") or "0")),
        city=(r.get("city") or "")[:150],
        client=(r.get("client") or "")[:300],
        legal_address=(r.get("legal_address") or "")[:400],
        actual_address=(r.get("actual_address") or "")[:400],
        inn=(r.get("inn") or "")[:30],
        segment=(r.get("segment") or "")[:120],
        uploaded_by=user,
        batch_id=batch_id,
        is_confirmed=False,
    )


def _record_to_row(rec, idx):
    """DistributorRecord -> onizleme satiri (dict), React icin."""
    return {
        "index": idx,
        "distributor": rec.distributor,
        "type": rec.operation_type,
        "city": rec.city,
        "product": rec.product_name,
        "product_type": rec.product_type,
        "count": rec.count,
        "amount": float(rec.amount or 0),
        "client": rec.client,
        "legal_address": rec.legal_address,
        "actual_address": rec.actual_address,
        "inn": rec.inn,
        "segment": rec.segment,
    }


_DEPO_PAGE_SIZE = 200
#200 de backed kaydet ve yenisini getir


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def depo_upload_preview_api(request):
    """
    Excel'i parse et, satirlari DistributorRecord'a batch_id + is_confirmed=False
    (taslak) olarak yaz. Ozet + ilk sayfa + batch_id + toplam dondur.
    """
    from .depo_upload_service import DepoUploadService
    from .models import DistributorRecord
    from datetime import datetime as _dt

    distributor = (request.POST.get("distributor") or "").strip()
    country = (request.POST.get("country") or "").strip()
    begin_date_str = (request.POST.get("begin_date") or "").strip()
    end_date_str = (request.POST.get("end_date") or "").strip()
    excel_file = request.FILES.get("excel_file")

    if not request.user.is_staff:
        uc = (getattr(request.user, "country", "") or "").strip()
        if uc:
            country = uc

    if not excel_file:
        return Response({"error": "Выберите файл Excel."}, status=400)
    if not distributor or not country:
        return Response({"error": "Заполните дистрибьютора и страну."}, status=400)

    begin_date = end_date = None
    try:
        if begin_date_str:
            begin_date = _dt.strptime(begin_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = _dt.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Неверный формат даты."}, status=400)

    sheet, err = _open_sheet(excel_file)
    if err:
        return Response({"error": err}, status=400)

    file_name = getattr(excel_file, "name", "") or ""
    service = DepoUploadService()
    result = service.preview(sheet, file_name, distributor, "",
                             sheet.max_row, sheet.max_column)
    if result.error:
        return Response({"error": result.error}, status=400)
    if not result.rows:
        return Response({"error": "В файле не найдено ни одной строки с данными."}, status=400)

    
    DistributorRecord.objects.filter(
        uploaded_by=request.user, is_confirmed=False
    ).delete()

    #yeni
    batch_id = _uuid.uuid4().hex
    op_code = "SALE" if (result.stock_sales_type or "").upper().startswith("SAL") else "STOCK"

    objs = [
        _depo_row_to_record(r, batch_id, distributor, country, op_code,
                            begin_date, end_date, request.user)
        for r in result.rows
    ]
    DistributorRecord.objects.bulk_create(objs, batch_size=1000)

    total = len(objs)
    
    first = DistributorRecord.objects.filter(batch_id=batch_id).order_by("id")[:_DEPO_PAGE_SIZE]
    rows = [_record_to_row(rec, i + 1) for i, rec in enumerate(first)]

    return Response({
        "batch_id": batch_id,
        "rows": rows,
        "page": 1,
        "page_size": _DEPO_PAGE_SIZE,
        "total_rows": total,
        "num_pages": (total + _DEPO_PAGE_SIZE - 1) // _DEPO_PAGE_SIZE,
        "type": result.stock_sales_type,
        "summary": {
            "solgar_count": result.total_count_solgar,
            "solgar_amount": round(result.total_amount_solgar, 2),
            "bounty_count": result.total_count_bounty,
            "bounty_amount": round(result.total_amount_bounty, 2),
        },
        "meta": {"distributor": distributor, "country": country,
                 "begin_date": begin_date_str, "end_date": end_date_str},
        "error": "",
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def depo_upload_page_api(request):
    """Bir batch'in belirli sayfasini dondur (DB pagination)."""
    from .models import DistributorRecord

    batch_id = (request.GET.get("batch_id") or "").strip()
    try:
        page = max(1, int(request.GET.get("page", "1")))
    except (TypeError, ValueError):
        page = 1

    if not batch_id:
        return Response({"error": "batch_id gerekli."}, status=400)

    qs = DistributorRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).order_by("id")
    total = qs.count()
    offset = (page - 1) * _DEPO_PAGE_SIZE
    page_recs = qs[offset:offset + _DEPO_PAGE_SIZE]
    rows = [_record_to_row(rec, offset + i + 1) for i, rec in enumerate(page_recs)]

    return Response({
        "batch_id": batch_id,
        "rows": rows,
        "page": page,
        "page_size": _DEPO_PAGE_SIZE,
        "total_rows": total,
        "num_pages": (total + _DEPO_PAGE_SIZE - 1) // _DEPO_PAGE_SIZE,
        "error": "",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def depo_upload_save_api(request):
    """Batch'i onayla (is_confirmed=True). Kayit zaten yapildi, sadece onay."""
    from .models import DistributorRecord

    data = request.data or {}
    batch_id = (data.get("batch_id") or "").strip()
    if not batch_id:
        return Response({"error": "batch_id gerekli."}, status=400)

    updated = DistributorRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).update(is_confirmed=True)

    if updated == 0:
        return Response({"error": "Onaylanacak taslak bulunamadi (suresi dolmus olabilir)."}, status=400)

    return Response({"created": updated, "error": ""})


# ==================== Eczane (parametrik parser) upload API - batch/taslak ====================
# Distributor depo-upload akisinin eczane versiyonu. pharmacy_parser +
# SIMPLE_CONFIGS kullanir, SalesRecord'a batch_id + is_confirmed=False yazar.

import uuid as _ph_uuid
from datetime import datetime as _ph_dt

_PHARM_PAGE_SIZE = 200


def _ph_open_sheet(excel_file):
    """xlsx (openpyxl 2D liste - hizli) / xls (xlrd) oku. (sheet, err)."""
    import io
    data = excel_file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
        ws = wb.active
        grid = [list(r) for r in ws.iter_rows(values_only=True)]
        wb.close()
        return _GridSheet(grid), None
    except Exception:
        pass
    try:
        import xlrd
        book = xlrd.open_workbook(file_contents=data)
        s = book.sheet_by_index(0)
        grid = [[s.cell_value(r, c) for c in range(s.ncols)] for r in range(s.nrows)]
        return _GridSheet(grid), None
    except Exception as exc:
        return None, f"Excel okunamadi: {exc}"


def _ph_config_for(chain_name, file_name):
    """Zincir adi / dosya adindan SimpleVertical config bul."""
    from .pharmacy_simple_configs import SIMPLE_CONFIGS
    keys = (chain_name or "").upper(), (file_name or "").upper()
    for cfg_key, cfg in SIMPLE_CONFIGS.items():
        if cfg_key in keys[0] or cfg_key in keys[1]:
            return cfg
    return None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pharmacy_upload_preview_api(request):
    """
    Eczane Excel onizleme: parse -> SalesRecord'a batch_id + is_confirmed=False.
    multipart: excel_file, chain_name, country, report_date, main_group
    """
    from .pharmacy_parser import PharmacyParser
    from .models import SalesRecord
    from decimal import Decimal as _Dec
    from django.db import transaction as _txn

    chain_name = (request.POST.get("chain_name") or "").strip()
    country = (request.POST.get("country") or "").strip()
    report_date_str = (request.POST.get("report_date") or "").strip()
    main_group = (request.POST.get("main_group") or "").strip()
    excel_file = request.FILES.get("excel_file")

    if not request.user.is_staff:
        uc = (getattr(request.user, "country", "") or "").strip()
        if uc:
            country = uc

    if not excel_file:
        return Response({"error": "Выберите файл Excel."}, status=400)
    if not chain_name or not country or not report_date_str:
        return Response({"error": "Заполните сеть, страну и дату отчёта."}, status=400)

    try:
        report_date = _ph_dt.strptime(report_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Неверный формат даты."}, status=400)

    file_name = getattr(excel_file, "name", "") or ""

    sheet, err = _ph_open_sheet(excel_file)
    if err:
        return Response({"error": err}, status=400)

    from .pharmacy_all_configs import parse_chain
    parsed = parse_chain(sheet, chain_name or file_name, main_group, sheet.max_row, sheet.max_column)
    if parsed is None:
        return Response({"error": f"'{chain_name}' için parse konfigürasyonu bulunamadı."}, status=400)
    if not parsed:
        return Response({"error": "В файле не найдено ни одной строки с данными."}, status=400)

    def _brand(product):
        p = (product or "").upper()
        if "БАУНТИ" in p or "BOUNTY" in p or "НЭЙЧЕС" in p:
            return "BOUNTY"
        return "SOLGAR"

    def _int(v):
        try:
            return int(str(v).split(".")[0].replace(" ", "")) if v else 0
        except (ValueError, TypeError):
            return 0

    def _dec(v):
        try:
            return _Dec(str(v).replace(" ", "").replace(",", ".")) if v else _Dec("0")
        except Exception:
            return _Dec("0")

    batch_id = _ph_uuid.uuid4().hex
    total_solgar_c = total_bounty_c = 0
    objs = []
    for r in parsed:
        brand = _brand(r.get("PRODUCT"))
        cnt = _int(r.get("COUNT"))
        if brand == "BOUNTY":
            total_bounty_c += cnt
        else:
            total_solgar_c += cnt
        objs.append(SalesRecord(
            report_date=report_date, chain_name=chain_name, country=country,
            product_name=(r.get("PRODUCT") or "")[:300], brand=brand,
            pharmacy=(r.get("PHARMACY") or "")[:400], city=(r.get("CITY") or "")[:150],
            count=cnt, amount=_dec(r.get("AMOUNT")),
            remaining_count=_int(r.get("REMAINING_COUNT")),
            remaining_amount=_dec(r.get("REMAINING_AMOUNT")),
            aptekno=(r.get("APTEKNO") or "")[:120],
            salesreader=(r.get("SALESREADER") or "")[:400],
            subgroup=(r.get("SUBGROUP") or "")[:150],
            main_group=(r.get("MAINGROUP") or "")[:150],
            uploaded_by=request.user, batch_id=batch_id, is_confirmed=False,
        ))

    try:
        with _txn.atomic():
            SalesRecord.objects.filter(uploaded_by=request.user, is_confirmed=False).delete()
            SalesRecord.objects.bulk_create(objs, batch_size=5000)
    except Exception as exc:
        return Response({"error": f"Ошибка при подготовке: {exc}"}, status=500)

    total = len(objs)
    first = SalesRecord.objects.filter(batch_id=batch_id).order_by("id")[:_PHARM_PAGE_SIZE]
    rows = [_ph_row(rec, i + 1) for i, rec in enumerate(first)]

    return Response({
        "batch_id": batch_id, "rows": rows, "page": 1, "page_size": _PHARM_PAGE_SIZE,
        "total_rows": total, "num_pages": (total + _PHARM_PAGE_SIZE - 1) // _PHARM_PAGE_SIZE,
        "summary": {"solgar_count": total_solgar_c, "bounty_count": total_bounty_c},
        "meta": {"chain_name": chain_name, "country": country, "report_date": report_date_str},
        "error": "",
    })


def _ph_row(rec, idx):
    return {
        "index": idx, "product": rec.product_name, "brand": rec.brand,
        "pharmacy": rec.pharmacy, "aptekno": rec.aptekno, "city": rec.city,
        "count": rec.count, "amount": float(rec.amount or 0),
        "subgroup": rec.subgroup, "main_group": rec.main_group,
        "remaining_count": rec.remaining_count,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pharmacy_upload_page_api(request):
    """Batch'in bir sayfasi (DB pagination)."""
    from .models import SalesRecord
    batch_id = (request.GET.get("batch_id") or "").strip()
    try:
        page = max(1, int(request.GET.get("page", "1")))
    except (TypeError, ValueError):
        page = 1
    if not batch_id:
        return Response({"error": "batch_id gerekli."}, status=400)
    qs = SalesRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).order_by("id")
    total = qs.count()
    offset = (page - 1) * _PHARM_PAGE_SIZE
    recs = qs[offset:offset + _PHARM_PAGE_SIZE]
    rows = [_ph_row(rec, offset + i + 1) for i, rec in enumerate(recs)]
    return Response({
        "batch_id": batch_id, "rows": rows, "page": page, "page_size": _PHARM_PAGE_SIZE,
        "total_rows": total, "num_pages": (total + _PHARM_PAGE_SIZE - 1) // _PHARM_PAGE_SIZE,
        "error": "",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pharmacy_upload_save_api(request):
    """Batch'i onayla (is_confirmed=True)."""
    from .models import SalesRecord
    data = request.data or {}
    batch_id = (data.get("batch_id") or "").strip()
    if not batch_id:
        return Response({"error": "batch_id gerekli."}, status=400)
    updated = SalesRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).update(is_confirmed=True)
    if updated == 0:
        return Response({"error": "Onaylanacak taslak bulunamadi."}, status=400)
    return Response({"created": updated, "error": ""})




class _GridCell:
    __slots__ = ("value",)
    def __init__(self, value):
        self.value = value


class _GridSheet:
    """2D listeyi openpyxl-benzeri (cell(row=, column=)) arayuze sarar.
    Tum veri bellekte; cell() erisimi cok hizli (openpyxl cell() degil)."""
    def __init__(self, grid):
        self._g = grid
        self.max_row = len(grid)
        self.max_column = max((len(r) for r in grid), default=0)
    def cell(self, row, column):
        r, c = row - 1, column - 1
        if 0 <= r < len(self._g) and 0 <= c < len(self._g[r]):
            return _GridCell(self._g[r][c])
        return _GridCell(None)

#counrty e gore aliyoruz
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pharmacy_chains_api(request):
    from .pharmacy_country_chains import country_chains_for

    country = (request.GET.get("country") or "").strip()
    if not request.user.is_staff:
        uc = (getattr(request.user, "country", "") or "").strip()
        if uc:
            country = uc

    chains = country_chains_for(country)
    return Response({"chains": chains, "country": country})
