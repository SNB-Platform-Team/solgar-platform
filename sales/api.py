# ==================== 1C API (DRF) ====================

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


# ==================== Doctor Managerial API (DRF) ====================

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


# ==================== Pharmacy Managerial API (DRF) ====================

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


# ==================== Pharmacy Entry API (DRF) ====================

# Tabloda gosterilecek kolonlar (entry ekranindaki ana alanlar).
# match_key bir @property (DB kolonu degil), o yuzden liste disinda.
_PHARMACY_API_COLUMNS = [
    ("pharmacy_name", "Название"),
    ("country", "Страна"),
    ("region", "Регион"),
    ("city", "Город"),
    ("pharmacy_address", "Адрес"),
    ("group_company", "Сеть"),
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

    try:
        result = service.query(brand=brand, search=search, page=page)
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
    })


# ==================== Doctor Entry API (DRF) ====================

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
