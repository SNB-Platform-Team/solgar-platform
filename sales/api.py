#1c api
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from authorization.permissions import HasScreen
from .views import OneCService


ONEC_API_TABS = [
    {"key": "orders", "label": "Заказы"},
    {"key": "shipments", "label": "Поставки"},
    {"key": "sales", "label": "Продажи"},
    {"key": "residues", "label": "Свободные остатки"},
]


@api_view(["GET"])
@permission_classes([HasScreen("ONEC_STOCK")])
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
@permission_classes([HasScreen("DOCTOR_MGR")])
def doctor_managerial_api(request):
    """
    Doctor Managerial report API. Returns dropdown options plus, when run=1,
    a grouped/counted report (columns + rows) as JSON for the React frontend.

    Query params (all optional):
      run        - "1" to actually run the report (otherwise only options)
      brand, rep_type, parameter
      country, district, region, city, speciality, sub_speciality, clinic,
      medrep, activeness, begin, end

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
    district = (request.GET.get("district") or "").strip()
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
                country=country, district=district, region=region, city=city,
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
            "country": country, "district": district, "region": region, "city": city,
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
@permission_classes([HasScreen("PHARM_MGR")])
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
    ("id", "Id"),
    ("brand", "BRAND"),
    ("country", "Country"),
    ("area", "Area"),
    ("region", "Region"),
    ("city", "City"),
    ("district", "District"),
    ("metro", "METRO"),
    ("group_company", "GROUP COMPANY"),
    ("subgroup_company", "SUBGROUP COMPANY"),
    ("marketing_staff", "Marketing Staff"),
    ("pharmacy_address", "PHARMACY ADDRESS"),
    ("assortiment", "ASSORTMENT"),
    ("pharmacy_category", "PHARMACY CATEGORY"),
    ("pharmacy_type", "PHARMACY_TYPE"),
    ("promo", "PROMO"),
    ("pharmacy_activeness", "Pharmacy Activeness"),
    ("pharmacy_activation_date", "Pharmacy Activation Date"),
    ("pharmacy_response_person", "PHARM HEAD NAME"),
    ("pharmacy_tel", "Pharmacy Tel"),
    ("pharmacy_email", "Pharmacy Email"),
    ("comments", "Comments"),
    ("full_address", "Full Address"),
    ("building_type", "Building Type"),
    ("country_code", "Country Code"),
    ("administrative_area_name", "Administrative Area Name"),
    ("sub_administrative_area_name", "Sub Administrative Area Name"),
    ("street", "Street"),
    ("homenumber", "Home Number"),
    ("point_y", "point_y"),
    ("point_x", "point_x"),
    ("assortiment1", "OBF"),
    ("pharmacy_group", "Pharm Group"),
    ("sku", "SKU"),
    ("cornerNo", "Corner No"),
    ("pharmacy_id", "PHARMACY_ID"),
    ("entry_user", "Entry User"),
    ("entry_date", "Entry Date"),
    ("pharmacist_name_1", "Pharmacist Name 1"),
    ("pharmacy_home_tel", "Pharmacist1 Tel"),
    ("pharmacist_name_2", "Pharmacist Name 2"),
    ("pharmacy_work_tel", "Pharmacist2 Tel"),
]

PHARMACY_API_BRANDS = [
    {"value": "SOLGAR", "label": "SOLGAR"},
    {"value": "BOUNTY", "label": "NATURES BOUNTY"},
]


@api_view(["GET"])
@permission_classes([HasScreen("PHARMACY")])
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

    # Satir-seviyesi guvenlik (doctor_api ile ayni mantik): medrep (Сотрудник,
    # is_staff=False) SADECE kendi aptekalarini gorur. Apteka tablosunda med.
    # temsilci kolonu 'marketing_staff'. Kisit SERVER tarafinda zorunlu — panel
    # kaldirmak tek basina yetmez, API dogrudan cagrilabilir. Admin/Menecer
    # (is_staff=True) icin kisit yok. Eslesme yoksa bos liste (guvenli taraf).
    user = getattr(request, "user", None)
    if user and user.is_authenticated and not user.is_staff:
        name = ""
        try:
            name = _medrep_name_from_email(getattr(user, "email", "") or "")
        except Exception:
            name = ""
        filters["marketing_staff"] = name or "\x00__no_medrep_match__"

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
    ("id", "ID"),
    ("brand", "Brand"),
    ("country", "Country"),
    ("area", "Area"),
    ("region", "Region"),
    ("district", "District"),
    ("city", "City"),
    ("activeness", "Activeness"),
    ("medrep", "Medrep"),
    ("doctor_date", "Activation Date"),
    ("doctor_name", "Doctor Name"),
    ("unified_specialty", "Унифицированная спец."),
    ("specialty", "Специальность"),
    ("position_regalia", "Должность"),
    ("category", "Category"),
    ("clinic_name", "Clinic Name"),
    ("clinic_status", "Clinic Category"),
    ("clinic_address", "Clinic Address"),
    ("clinic_count", "Clinic Count"),
    ("key_person", "Key Person"),
    ("doctor_tel", "Doctor Tel"),
    ("doctor_email", "Doctor Email"),
    ("full_address", "Full Address"),
    ("building_type", "Building Type"),
    ("country_code", "Country Code"),
    ("administrative_area_name", "Administrative Area Name"),
    ("sub_administrative_area_name", "Sub Administrative Area Name"),
    ("street", "Street"),
    ("homenumber", "Home Number"),
    ("point_y", "point_y"),
    ("point_x", "point_x"),
    ("entry_user", "Entry User"),
    ("entry_date", "Entry Date"),
    ("clinic_name1", "Clinic Name 1"),
]

# doctor_data'da brand tam isim olarak saklanir (SOLGAR / NATURES BOUNTY).
DOCTOR_API_BRANDS = [
    {"value": "", "label": "Все"},
    {"value": "SOLGAR", "label": "SOLGAR"},
    {"value": "NATURES BOUNTY", "label": "NATURES BOUNTY"},
]


@api_view(["GET"])
@permission_classes([HasScreen("DOCTOR")])
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

    # Satir-seviyesi guvenlik: medrep (Сотрудник, is_staff=False) SADECE kendi
    # doktorlarini gorur (medrep = kendi adi). Bu kisit SERVER tarafinda zorunlu
    # kilinir — frontend'de filtre panelini kaldirmak tek basina yeterli degil,
    # cunku medrep API'yi dogrudan cagirip baskasinin doktorlarini cekebilir.
    # Admin/Menecer (is_staff=True) icin kisit yok, hepsini gorur.
    force_medrep = None
    user = getattr(request, "user", None)
    if user and user.is_authenticated and not user.is_staff:
        name = ""
        try:
            name = _medrep_name_from_email(getattr(user, "email", "") or "")
        except Exception:
            name = ""
        # Eslesme yoksa: eslesmeyecek bir sentinel -> bos liste (guvenli taraf).
        force_medrep = name or "\x00__no_medrep_match__"

    try:
        if force_medrep is not None:
            result = service.query(
                brand=brand, search=search, page=page, medrep=force_medrep
            )
        else:
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
@permission_classes([HasScreen("CHAIN_REPORT")])
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
            region=region, district=district,
            page=page, page_size=_CHAIN_REPORT_PAGE_SIZE, **filters
        )
    except Exception as exc:
        return Response({"error": f"Ошибка отчета: {exc}"}, status=500)

    columns = ["Компания", "Наименование", "Сеть", "Дата", "Город",
               "Аптека", "Кол-во", "Сумма"]

    # Tarih araligi zorunlu — secilmemisse bos sonuc + bilgi mesaji.
    if result.get("needs_date_range"):
        return Response({
            "brands": CHAIN_REPORT_BRANDS_API,
            "columns": columns,
            "rows": [],
            "total_rows": 0,
            "page": 1, "num_pages": 1,
            "has_prev": False, "has_next": False,
            "message": "Выберите период (дата с и дата по) для формирования отчёта.",
            "needs_date_range": True,
            "totals": {"solgar_count": 0, "solgar_amount": 0,
                       "bounty_count": 0, "bounty_amount": 0},
            "f": {
                "brand": request.GET.get("brand", ""), "chain_name": request.GET.get("chain_name", ""),
                "country": request.GET.get("country", ""), "city": request.GET.get("city", ""),
                "date_from": date_from, "date_to": date_to, "search": search,
            },
        })

    # service dict satirlari (kaynak-agnostik) -> tablo satirlari.
    rows = []
    for r in result["rows"]:
        rd = r.get("report_date")
        rows.append([
            _json_safe(r.get("brand_label", "")),
            _json_safe(r.get("product_name", "")),
            _json_safe(r.get("chain_name", "")),
            rd.strftime("%d.%m.%Y") if rd else "",
            _json_safe(r.get("city", "") or ""),
            _json_safe(r.get("pharmacy", "") or ""),
            _json_safe(r.get("count", 0)),
            _json_safe(r.get("amount", 0)),
        ])

    return Response({
        "brands": CHAIN_REPORT_BRANDS_API,
        "columns": columns,
        "rows": rows,
        "total_rows": result["total_rows"],
        "page": result["page"],
        "num_pages": result["num_pages"],
        "has_prev": result["has_prev"],
        "has_next": result["has_next"],
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
@permission_classes([HasScreen("SALES_OBS")])
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
        # Tarih araligi limiti: distributör raporlari max 3 ay.
        _rng_err = _date_range_error(begin, end, 3)
        if _rng_err:
            error = _rng_err
        b = begin.replace("-", "")
        e = end.replace("-", "")
        if not error and len(b) == 8 and len(e) == 8 and b.isdigit() and e.isdigit():
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
@permission_classes([HasScreen("SALES_OBS")])
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


def _dashboard_my_cards(request):
    """Giris yapan medrep'in KENDI apteka + doktor kayit sayilari.

    Sadece medrep (Сотрудник, is_staff=False) icin dondurulur; admin/menecer
    icin None (frontend kartlari gostermez). Sayim medrep satir-filtresiyle
    birebir ayni: apteka marketing_staff = kendi adi, doctor medrep = kendi
    adi, status=1. Isim solgar_org.employees'ten (me_api ile ayni kaynak).
    Kullaniciya ozel oldugu icin dashboard'in global cache'inden BAGIMSIZ,
    her istekte hesaplanir. Eslesme yoksa (ad bos) 0."""
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated) or user.is_staff:
        return None

    try:
        name = _medrep_name_from_email(getattr(user, "email", "") or "")
    except Exception:
        name = ""
    if not name:
        return {"medrep_name": "", "pharmacies": 0, "doctors": 0}

    from django.db.models import Count

    def _norm(v):
        """Bos/None degerleri tek bir '—' etiketinde topla."""
        s = (str(v).strip() if v is not None else "")
        return s or "—"

    # --- Apteka: toplam + region x category kirilimi (SOLGAR+BOUNTY birlesik) ---
    # Yoneticinin SQL'i: union all (solgar+bounty) -> group by region, category.
    pharmacies = 0
    ph_breakdown = {}  # (region, category) -> count
    try:
        from .repositories import PharmacyRepository
        pr = PharmacyRepository()
        for brand in ("SOLGAR", "BOUNTY"):
            model = pr._model_for(brand)
            qs = (model.objects.filter(status=1, marketing_staff=name)
                  .values("region", "pharmacy_category")
                  .annotate(c=Count("*")))
            for row in qs:
                key = (_norm(row["region"]), _norm(row["pharmacy_category"]))
                ph_breakdown[key] = ph_breakdown.get(key, 0) + row["c"]
                pharmacies += row["c"]
    except Exception:
        pharmacies = 0
        ph_breakdown = {}

    # --- Doktor: toplam + region x category kirilimi ---
    doctors = 0
    dr_breakdown = {}
    try:
        from .models import Doctor
        qs = (Doctor.objects.filter(status=1, medrep=name)
              .values("region", "category")
              .annotate(c=Count("*")))
        for row in qs:
            key = (_norm(row["region"]), _norm(row["category"]))
            dr_breakdown[key] = dr_breakdown.get(key, 0) + row["c"]
            doctors += row["c"]
    except Exception:
        doctors = 0
        dr_breakdown = {}

    def _rows(bd):
        # category'ye gore sirala (SQL'deki 'order by category'), sonra region.
        return [
            {"region": r, "category": cat, "count": n}
            for (r, cat), n in sorted(bd.items(), key=lambda kv: (kv[0][1], kv[0][0]))
        ]

    return {
        "medrep_name": name,
        "pharmacies": pharmacies,
        "doctors": doctors,
        "pharmacy_breakdown": _rows(ph_breakdown),
        "doctor_breakdown": _rows(dr_breakdown),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """
    Dashboard summary API: headline counters, top chains, monthly sales trend.
    Cached 10 minutes.

    `my_cards` (medrep'in kendi apteka/doktor sayisi) kullaniciya ozeldir ve
    global cache disinda, her istekte hesaplanir; admin/menecer icin None.
    """
    from .services import ReportService, PharmacyViewService, DoctorViewService

    cached = _dash_cache.get("dashboard_summary_v1")
    if cached is not None:
        payload = dict(cached)
        payload["my_cards"] = _dashboard_my_cards(request)
        return Response(payload)

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
    payload = dict(payload)
    payload["my_cards"] = _dashboard_my_cards(request)
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
@permission_classes([HasScreen("SALES_UPLOAD")])
def sales_upload_options_api(request):
    """Dropdown options for the sales upload screen: active chains + countries."""
    from .models import ChainDefinition
    try:
        from .views import COUNTRIES
    except Exception:
        COUNTRIES = []
    chains = list(
        ChainDefinition.objects.filter(is_active=True, source_type=ChainDefinition.SourceType.PHARMACY).values_list("name", flat=True)
    )
    return Response({"chains": sorted(chains), "countries": list(COUNTRIES)})


@api_view(["POST"])
@permission_classes([HasScreen("SALES_UPLOAD")])
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
@permission_classes([HasScreen("SALES_UPLOAD")])
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
@permission_classes([HasScreen("DIST_UPLOAD")])
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
@permission_classes([HasScreen("DIST_UPLOAD")])
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
@permission_classes([HasScreen("DIST_UPLOAD")])
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
@permission_classes([HasScreen("PHARMACY")])
def pharmacy_filter_options_api(request):
    """
    Dropdown data for the Pharmacy screen filters. Brand-scoped.

    Two modes:
      1) No `level` param: returns ALL top-level lists at once (initial load) --
         countries, chains, categories, types, promos, marketing_staff. Cached.
      2) With `level` param: returns ONE cascading list based on parent values
         (level=area/region/city/metro/subchain), mirroring the Java AJAX
         cascade. Used when the user picks a parent value.

    Query params:
      brand (SOLGAR/BOUNTY), level, country, area, region, city, group_company
    """
    from .repositories import PharmacyRepository
    from django.core.cache import cache

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
            options = repo.subchains(brand, group_company=group_company, country=country)
        else:
            options = []
        return Response({"level": level, "options": list(options)})

    # Level'siz tam liste: en agir kisim (6 distinct), cache'le (15 dk).
    cache_key = f"pharm_filter_opts_{brand}_{country}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    def _safe(fn, *a, **kw):
        try:
            return list(fn(*a, **kw))
        except Exception:
            return []

    result = {
        "countries": _safe(repo.countries, brand),
        "chains": _safe(repo.chains, brand, country=country),
        "categories": _safe(repo.pharmacy_categories, brand),
        "types": _safe(repo.pharmacy_types, brand),
        "promos": _safe(repo.promos, brand),
        "marketing_staff": _safe(repo.marketing_staff, brand),
        "assortiments": _safe(repo.assortiments, brand),
        "skus": _safe(repo.skus, brand),
        "statuses": _safe(repo.pharmacy_statuses, brand, country=country),
    }
    cache.set(cache_key, result, 900)
    return Response(result)




# ==================== Doctor Filter Options API (cascading dropdowns) ====================

@api_view(["GET"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_filter_options_api(request):
    """
    Dropdown data for the Doctor screen filters.

    Two modes:
      1) No `level`: all top-level lists (countries, specialties,
         unified_specialties, medreps). Cached.
      2) With `level` (area/region/city): one cascading list narrowed by
         parent selections (country -> area -> region -> city).

    Query params: level, country, area, region
    """
    from .repositories import DoctorRepository
    from django.core.cache import cache

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
        elif level == "metro":
            # Метро/Округ — prm_sales_district (filtresiz tum liste).
            options = repo.metros(country=country, area=area, region=region)
        else:
            options = []
        return Response({"level": level, "options": list(options)})

    # Level'siz tam liste: cache'le (15 dk).
    cached = cache.get("doctor_filter_opts")
    if cached is not None:
        return Response(cached)

    def _safe(fn, *a, **kw):
        try:
            return list(fn(*a, **kw))
        except Exception:
            return []

    result = {
        "countries": _safe(repo.countries),
        "specialties": _safe(repo.specialties),
        "unified_specialties": _safe(repo.unified_specialties),
        "medreps": _safe(repo.medreps),
        "clinics": _safe(repo.clinic_names),
    }
    cache.set("doctor_filter_opts", result, 900)
    return Response(result)

# ==================== Current user (auth check) API ====================


def _medrep_name_from_email(email: str) -> str:
    """SSO mailinden medrep adini dondur (solgar_org.employees).

    Eslesme: LOWER(TRIM(EMPLOYEE_EMAIL)) = LOWER(TRIM(email)), sadece
    EMPLOYEE_ACTIVE='ACTIVE'. Birden fazla eslesirse ilk (id'ye gore).
    Bulunamazsa ''. solgar_org'a solgar_app'in SELECT yetkisi olmayabilir,
    bu yuzden solgar_prm gibi refdb baglantisindan okunur."""
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return ""
    from django.db import connections
    sql = (
        "SELECT EMPLOYEE_NAME FROM solgar_org.employees "
        "WHERE LOWER(TRIM(EMPLOYEE_EMAIL)) = %s "
        "AND UPPER(TRIM(EMPLOYEE_ACTIVE)) = 'ACTIVE' "
        "AND EMPLOYEE_NAME IS NOT NULL AND EMPLOYEE_NAME <> '' "
        "ORDER BY id LIMIT 1"
    )
    with connections["refdb"].cursor() as cur:
        cur.execute(sql, [email])
        row = cur.fetchone()
    return str(row[0]).strip() if row and row[0] else ""


@api_view(["GET"])
@permission_classes([AllowAny])
def me_api(request):
    """
    Returns the current user's auth state. React calls this on load to decide
    whether to show the app or redirect to login. AllowAny so it can be called
    while logged out (returns authenticated: false instead of 403).
    """
    if request.user and request.user.is_authenticated:
        # React menuyu/route'u filtrelesin diye erisilebilir ekran kodlari.
        # Superuser -> hepsi; access_level olan -> o seviyenin ekranlari;
        # digeri -> bos. (authorization.permissions._user_screen_codes ile
        # ayni kaynak, API korumasiyla tutarli.)
        try:
            from authorization.permissions import _user_screen_codes
            screens = sorted(_user_screen_codes(request.user))
        except Exception:
            screens = []

        # Мед. представитель: medrep (Сотрудник, is_staff=False) kullanicinin
        # SSO maili solgar_org.employees'teki ACTIVE bir medrep ile eslesirse
        # EMPLOYEE_NAME doner. Frontend bu ismi doktor sayfasinda otomatik
        # doldurup disable eder. Eslesme yoksa "" (bos ama yine disable).
        # Admin/Menecer (is_staff=True) icin gonderilmez -> onlar serbest secer.
        medrep_name = ""
        if not request.user.is_staff:
            try:
                medrep_name = _medrep_name_from_email(
                    getattr(request.user, "email", "") or ""
                )
            except Exception:
                medrep_name = ""

        return Response({
            "authenticated": True,
            "username": request.user.username,
            "display_name": request.user.get_full_name() or request.user.username,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "country": getattr(request.user, "country", "") or "",
            "medrep_name": medrep_name,
            "screens": screens,
        })
    return Response({"authenticated": False})


# ==================== Chain Report Filter Options API (cascading) ====================

@api_view(["GET"])
@permission_classes([HasScreen("CHAIN_REPORT")])
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
@permission_classes([HasScreen("EMPLOYEES")])
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
    Country dropdown options from solgar_prm.prm_sales_addresses, scoped to
    the current user:
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
    from .repositories import _prm_countries

    user = request.user
    is_staff = bool(user.is_staff)
    user_country = (getattr(user, "country", "") or "").strip()

    # Full country list from prm_sales_addresses (DISTINCT country) — ayni
    # kaynak Страна -> Область -> ... kaskadiyla. prm_countries prod'da yok.
    try:
        all_countries = _prm_countries()
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
@permission_classes([HasScreen("ONEC_STOCK")])
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
    """Yuklenen Excel'i oku (xlsx: openpyxl, xls: xlrd, xlsb: pyxlsb). (sheet, err) doner."""
    import io
    data = excel_file.read()
    # 1) openpyxl (xlsx)
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        return wb.active, None
    except Exception:
        pass
    # 2) xlrd (eski xls)
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
    except Exception:
        pass
    # 3) pyxlsb (xlsb - binary; uzanti .xls olsa da icerik xlsb olabilir)
    try:
        import pyxlsb
        wb = pyxlsb.open_workbook(io.BytesIO(data))
        sheet_name = wb.sheets[0]
        ws = wb.get_sheet(sheet_name)
        # Tum satirlari 2D listeye oku (pyxlsb satir satir iterator)
        grid = []
        for row in ws.rows():
            # row: list[Cell(r,c,v)]; max kolona kadar doldur
            cells = {}
            maxc = 0
            for cell in row:
                cells[cell.c] = cell.v
                if cell.c > maxc:
                    maxc = cell.c
            grid.append([cells.get(i) for i in range(maxc + 1)])

        max_col = max((len(r) for r in grid), default=0)

        class _C:
            def __init__(self, v): self.value = v

        class _WX:
            def __init__(self, g, mc):
                self._g = g
                self.max_row = len(g)
                self.max_column = mc
            def cell(self, row, column):
                r, c = row - 1, column - 1
                if 0 <= r < len(self._g) and 0 <= c < len(self._g[r]):
                    return _C(self._g[r][c])
                return _C(None)

        return _WX(grid, max_col), None
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
@permission_classes([HasScreen("DIST_UPLOAD")])
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
@permission_classes([HasScreen("DIST_UPLOAD")])
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


# Distributor upload onayinda yazilacak hedef: solgar_stk.stock_sales_table
# (legacy, 14M satir, refdb). id auto_increment -> atlanir. uploadDate NOW().
_STOCK_INSERT_SQL = (
    "INSERT INTO solgar_stk.stock_sales_table "
    "(status, distributor, optype, city, product, product_type, count, amount, "
    " rep_begin_date, rep_end_date, client, legalAddress, actualAddress, INN, "
    " segment, uploadDate) "
    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
)
# operation_type (SALE/STOCK) -> legacy optype ('SALE'->'SALES')
_DEPO_OP_TO_LEGACY = {"SALE": "SALES", "STOCK": "STOCK"}
# brand -> legacy product_type kodu (SL/BN/OS)
_DEPO_BRAND_TO_PTYPE = {"SOLGAR": "SL", "BOUNTY": "BN", "OTHER": "OS"}


@api_view(["POST"])
@permission_classes([HasScreen("DIST_UPLOAD")])
def depo_upload_save_api(request):
    """
    Distributor upload ONAY: taslak satirlari (DistributorRecord) okur ve
    solgar_stk.stock_sales_table'a (legacy) yazar. Basarili olunca taslaklari
    siler. Ayni distributor+donem zaten varsa tekrar yukleme ENGELLENIR.
    stock_sales_table'da ID eslesme YOK — duz INSERT.
    """
    from .models import DistributorRecord
    from django.db import connections, transaction as _txn
    import datetime as _d

    data = request.data or {}
    batch_id = (data.get("batch_id") or "").strip()
    if not batch_id:
        return Response({"error": "batch_id gerekli."}, status=400)

    drafts = list(DistributorRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).order_by("id"))
    if not drafts:
        return Response({"error": "Onaylanacak taslak bulunamadi (suresi dolmus olabilir)."}, status=400)

    distributor = drafts[0].distributor or ""
    op_code = (drafts[0].operation_type or "").upper()
    legacy_op = _DEPO_OP_TO_LEGACY.get(op_code, op_code)
    begins = sorted({d.begin_date for d in drafts if d.begin_date})
    ends = sorted({d.end_date for d in drafts if d.end_date})
    bdate = begins[0] if begins else None
    edate = ends[-1] if ends else None

    # --- re-upload kontrolu: ayni distributor+optype+donem var mi? ---
    try:
        with connections["refdb"].cursor() as cur:
            cur.execute(
                "SELECT 1 FROM solgar_stk.stock_sales_table "
                "WHERE distributor = %s AND optype = %s "
                "  AND rep_begin_date = %s AND rep_end_date = %s LIMIT 1",
                [distributor, legacy_op, str(bdate), str(edate)],
            )
            if cur.fetchone():
                return Response({"error": (
                    f"Загрузка заблокирована: данные по «{distributor}» "
                    f"({legacy_op}) за период {bdate}—{edate} уже есть в базе. "
                    f"Повторная загрузка не допускается."
                )}, status=400)
    except Exception as exc:
        return Response({"error": f"Ошибка проверки дублей: {exc}"}, status=500)

    # --- INSERT tuple'lari ---
    now = _d.datetime.now()

    def _amt(v):
        try:
            from decimal import Decimal as _Dec
            return f"{_Dec(str(v or 0)):.2f}"
        except Exception:
            return "0.00"

    rows = []
    for d in drafts:
        ptype = _DEPO_BRAND_TO_PTYPE.get((d.brand or "").upper(),
                                         (d.product_type or "SL")[:2].upper())
        rows.append((
            "1",                                   # status (NOT NULL, hep '1')
            (d.distributor or "")[:45],            # distributor (NOT NULL)
            legacy_op[:5],                         # optype (NOT NULL)
            (d.city or "")[:100],                  # city (NOT NULL)
            (d.product_name or "")[:255],          # product (NOT NULL)
            ptype,                                 # product_type (NOT NULL)
            int(d.count or 0),                     # count (NOT NULL)
            _amt(d.amount),                        # amount
            str(d.begin_date) if d.begin_date else None,  # rep_begin_date
            str(d.end_date) if d.end_date else None,      # rep_end_date
            (d.client or "")[:255] or None,        # client
            (d.legal_address or "")[:255] or None, # legalAddress
            (d.actual_address or "")[:255] or None,# actualAddress
            (d.inn or "")[:255] or None,           # INN
            (d.segment or "")[:255] or None,       # segment
            now,                                   # uploadDate (NOT NULL, PK)
        ))

    # --- INSERT (refdb transaction, chunk'li) ---
    try:
        with _txn.atomic(using="refdb"):
            with connections["refdb"].cursor() as cur:
                CH = 5000
                for i in range(0, len(rows), CH):
                    cur.executemany(_STOCK_INSERT_SQL, rows[i:i + CH])
    except Exception as exc:
        return Response({"error": f"Ошибка записи в базу: {exc}"}, status=500)

    # Basarili -> taslaklari sil
    DistributorRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).delete()

    return Response({"created": len(rows), "error": ""})


# ==================== Eczane (parametrik parser) upload API - batch/taslak ====================
# Distributor depo-upload akisinin eczane versiyonu. pharmacy_parser +
# SIMPLE_CONFIGS kullanir, SalesRecord'a batch_id + is_confirmed=False yazar.

import uuid as _ph_uuid
from datetime import datetime as _ph_dt

_PHARM_PAGE_SIZE = 200


def _ph_open_sheet(excel_file, sheet_name=None):
    """xlsx (openpyxl) / xls (xlrd) oku. sheet_name verilirse o sayfa, yoksa ilk sayfa.
    (sheet, err) doner."""
    import io
    data = excel_file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
        if sheet_name and sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.active
        grid = [list(r) for r in ws.iter_rows(values_only=True)]
        wb.close()
        return _GridSheet(grid), None
    except Exception:
        pass
    try:
        import xlrd
        book = xlrd.open_workbook(file_contents=data)
        if sheet_name and sheet_name in book.sheet_names():
            s = book.sheet_by_name(sheet_name)
        else:
            s = book.sheet_by_index(0)
        grid = [[s.cell_value(r, c) for c in range(s.ncols)] for r in range(s.nrows)]
        return _GridSheet(grid), None
    except Exception as exc:
        return None, f"Excel okunamadi: {exc}"


def _ph_sheet_names(excel_file):
    """Yuklenen Excel'deki sayfa (sheet) isimlerini dondurur. (names, err)."""
    import io
    data = excel_file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
        names = list(wb.sheetnames)
        wb.close()
        return names, None
    except Exception:
        pass
    try:
        import xlrd
        book = xlrd.open_workbook(file_contents=data)
        return list(book.sheet_names()), None
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
@permission_classes([HasScreen("SALES_UPLOAD")])
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
    sheet_name = (request.POST.get("sheet_name") or "").strip()
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

    sheet, err = _ph_open_sheet(excel_file, sheet_name or None)
    if err:
        return Response({"error": err}, status=400)

    from .pharmacy_all_configs import parse_chain
    parsed = parse_chain(sheet, chain_name or file_name, main_group, sheet.max_row, sheet.max_column, country)
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
@permission_classes([HasScreen("SALES_UPLOAD")])
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


# Eczane upload onayinda yazilacak hedef: solgar_tst.sales_pharmacy (legacy,
# 45M satir, refdb uzerinden). id/creation_time/modification_time otomatik.
_PHARM_INSERT_SQL = (
    "INSERT INTO solgar_tst.sales_pharmacy "
    "(main_group, sub_group, pharmacy_address, product_Name, pharmacy_no, "
    " sales_count, sales_amount, sales_date, sales_reader, city, "
    " product_type, reader_id, pharm_id, product_id, country, "
    " remaining_count, remaining_amount) "
    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
)

# brand -> product_type kodu (legacy _BRAND_MAP ile ayni: SL/BN/OS)
_PH_BRAND_TO_PTYPE = {"SOLGAR": "SL", "BOUNTY": "BN", "OTHER": "OS"}


def _ph_norm(s):
    """Eslesme icin normalize: trim, upper, ic bosluklari tek bosluga indir."""
    return " ".join((s or "").strip().upper().split())


@api_view(["POST"])
@permission_classes([HasScreen("SALES_UPLOAD")])
def pharmacy_upload_save_api(request):
    """
    Eczane upload ONAY: taslak satirlari (sales_record) okur, reader_id /
    pharm_id / product_id'yi referans tablolardan cozer ve
    solgar_tst.sales_pharmacy'ye (legacy) yazar. Basarili olunca taslaklari
    siler. sales_record ARTIK kalici veri degil, sadece onizleme tamponu.

    ID eslesme kurallari (Olga/DBA):
      reader_id  = sales_address_group.id  (sales_reader = SALESREADER,
                   main_group esit, processed=1, online tablosunda OLMAYAN)
      pharm_id   = o reader satirinin marketing kolonu (SL->marketing_id,
                   BN->marketing_id_nb), >0 ise; yoksa 0
      product_id = sales_product_group.id  (product_sales_name = PRODUCT,
                   product_type esit); yoksa 0
    Ayni sebeke+tarih zaten varsa tekrar yukleme ENGELLENIR.
    """
    from .models import SalesRecord
    from django.db import connections, transaction as _txn
    import datetime as _d

    data = request.data or {}
    batch_id = (data.get("batch_id") or "").strip()
    if not batch_id:
        return Response({"error": "batch_id gerekli."}, status=400)

    drafts = list(SalesRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).order_by("id"))
    if not drafts:
        return Response({"error": "Onaylanacak taslak bulunamadi."}, status=400)

    # Bu batch'in sebeke ve tarih(ler)i
    chain_name = drafts[0].chain_name or ""
    report_dates = sorted({d.report_date for d in drafts if d.report_date})

    # --- re-upload kontrolu: ayni sebeke+tarih sales_pharmacy'de var mi? ---
    try:
        with connections["refdb"].cursor() as cur:
            for rd in report_dates:
                cur.execute(
                    "SELECT 1 FROM solgar_tst.sales_pharmacy "
                    "WHERE main_group = %s AND DATE(sales_date) = %s LIMIT 1",
                    [chain_name, str(rd)],
                )
                if cur.fetchone():
                    return Response({"error": (
                        f"Загрузка заблокирована: данные по сети «{chain_name}» "
                        f"за {rd} уже есть в базе. Повторная загрузка не допускается."
                    )}, status=400)
    except Exception as exc:
        return Response({"error": f"Ошибка проверки дублей: {exc}"}, status=500)

    # --- lookup dict'leri (2 sorgu, sebeke'ye gore daraltilmis) ---
    # reader/pharm: sales_address_group (processed=1, chain esit, online haric)
    addr_map = {}  # norm(sales_reader) -> (id, marketing_id, marketing_id_nb)
    product_map = {}  # (ptype, norm(product_sales_name)) -> id
    try:
        with connections["refdb"].cursor() as cur:
            cur.execute(
                "SELECT g.id, g.sales_reader, g.marketing_id, g.marketing_id_nb "
                "FROM solgar_tst.sales_address_group g "
                "WHERE g.processed = 1 AND g.main_group = %s "
                "  AND g.id NOT IN (SELECT id FROM solgar_tst.sales_address_group_online)",
                [chain_name],
            )
            for gid, sreader, mid, mid_nb in cur.fetchall():
                k = _ph_norm(sreader)
                if k and k not in addr_map:
                    addr_map[k] = (gid, int(mid or 0), int(mid_nb or 0))

            cur.execute(
                "SELECT id, product_type, product_sales_name "
                "FROM solgar_tst.sales_product_group"
            )
            for pid, ptype, pname in cur.fetchall():
                k = ((ptype or "").strip().upper(), _ph_norm(pname))
                if k[1] and k not in product_map:
                    product_map[k] = pid
    except Exception as exc:
        return Response({"error": f"Ошибка загрузки справочников: {exc}"}, status=500)

    # --- her taslak satiri cozup INSERT tuple'i olustur ---
    def _amt(v):
        try:
            from decimal import Decimal as _Dec
            return f"{_Dec(str(v or 0)):.2f}"
        except Exception:
            return "0.00"

    rows = []
    for d in drafts:
        ptype = _PH_BRAND_TO_PTYPE.get((d.brand or "").upper(), "SL")
        # reader_id + pharm_id
        reader_id = 0
        pharm_id = 0
        ar = addr_map.get(_ph_norm(d.salesreader))
        if ar:
            reader_id = ar[0]
            mk = ar[1] if ptype == "SL" else (ar[2] if ptype == "BN" else ar[1])
            pharm_id = mk if mk and mk > 0 else 0
        # product_id
        product_id = product_map.get((ptype, _ph_norm(d.product_name)), 0)

        sd = d.report_date
        sd_dt = _d.datetime.combine(sd, _d.time.min) if sd else None

        rows.append((
            (d.chain_name or "")[:100],           # main_group (NOT NULL)
            (d.subgroup or "")[:100] or None,      # sub_group
            (d.pharmacy or "")[:255] or None,      # pharmacy_address
            (d.product_name or "")[:255] or None,  # product_Name
            (d.aptekno or "")[:100] or None,       # pharmacy_no
            int(d.count or 0),                     # sales_count
            _amt(d.amount),                        # sales_amount (str)
            sd_dt,                                 # sales_date (NOT NULL, PK)
            (d.salesreader or "")[:255] or None,   # sales_reader
            (d.city or "")[:255] or None,          # city
            ptype,                                 # product_type
            int(reader_id or 0),                   # reader_id (NOT NULL)
            int(pharm_id or 0),                    # pharm_id (NOT NULL)
            int(product_id or 0),                  # product_id (NOT NULL)
            (d.country or "Russia")[:45],          # country
            int(d.remaining_count or 0),           # remaining_count
            _amt(d.remaining_amount),              # remaining_amount (str)
        ))

    # sales_date NOT NULL kontrolu (PK) — bos tarih tum batch'i patlatir
    if any(r[7] is None for r in rows):
        return Response({"error": "Bazı satırlarda rapor tarihi eksik."}, status=400)

    # --- INSERT (refdb transaction, chunk'li executemany) ---
    try:
        with _txn.atomic(using="refdb"):
            with connections["refdb"].cursor() as cur:
                CH = 5000
                for i in range(0, len(rows), CH):
                    cur.executemany(_PHARM_INSERT_SQL, rows[i:i + CH])
    except Exception as exc:
        # Prod'a yazilamadi -> taslaklar DURUR, kullanici tekrar deneyebilir.
        return Response({"error": f"Ошибка записи в базу: {exc}"}, status=500)

    # Basarili -> taslaklari sil (artik sales_record kalici degil)
    SalesRecord.objects.filter(
        batch_id=batch_id, uploaded_by=request.user, is_confirmed=False
    ).delete()

    return Response({"created": len(rows), "error": ""})




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

@api_view(["POST"])
@permission_classes([HasScreen("SALES_UPLOAD")])
def pharmacy_sheet_names_api(request):
    """Yuklenen Excel dosyasindaki sayfa (sheet) isimlerini dondurur.
    multipart: excel_file -> {"sheets": [...]}"""
    excel_file = request.FILES.get("excel_file")
    if not excel_file:
        return Response({"error": "Выберите файл Excel."}, status=400)
    names, err = _ph_sheet_names(excel_file)
    if err:
        return Response({"error": err}, status=400)
    return Response({"sheets": names, "error": ""})


#counrty e gore aliyoruz
@api_view(["GET"])
@permission_classes([HasScreen("SALES_UPLOAD")])
def pharmacy_chains_api(request):
    from .pharmacy_country_chains import country_chains_for

    country = (request.GET.get("country") or "").strip()
    if not request.user.is_staff:
        uc = (getattr(request.user, "country", "") or "").strip()
        if uc:
            country = uc

    chains = country_chains_for(country)
    return Response({"chains": chains, "country": country})




@api_view(["GET"])
@permission_classes([AllowAny])
def version_api(request):
    """Uygulama versiyonu (git commit hash)."""
    import os
    import subprocess

    version = os.environ.get("APP_VERSION", "").strip()

    if not version:
        try:
            from django.conf import settings
            vpath = os.path.join(settings.BASE_DIR, "version.txt")
            if os.path.exists(vpath):
                with open(vpath, encoding="utf-8") as f:
                    version = f.read().strip()
        except Exception:
            pass

    date = ""
    if not version:
        try:
            version = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            date = subprocess.check_output(
                ["git", "log", "-1", "--format=%cd", "--date=short"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except Exception:
            version = "dev"

    return Response({"version": version or "dev", "date": date})


# ==================== Doctor CRUD (ekle / guncelle / sil) ====================
# Java DoctorEntryUpdate'in is mantigi. doctor_data tablosuna (managed=False)
# yazar. Listeleme (doctor_api) + filtreler (doctor_filter_options_api) zaten var.

# Formdan gelip modele yazilabilecek alanlar (Java formu <-> model).
_DOCTOR_WRITABLE = [
    "brand", "country", "area", "region", "district", "city",
    "activeness", "medrep", "doctor_date", "doctor_name",
    "unified_specialty", "specialty", "position_regalia", "category",
    "clinic_name", "clinic_name1", "clinic_status", "clinic_address",
    "clinic_count", "key_person", "doctor_tel", "doctor_email",
    "full_address", "requested", "building_type", "country_code",
    "administrative_area_name", "sub_administrative_area_name",
    "street", "homenumber", "point_y", "point_x",
]


def _doctor_apply_fields(doc, data):
    """Form verisini Doctor nesnesine uygula (sadece izinli alanlar)."""
    for f in _DOCTOR_WRITABLE:
        if f in data:
            val = data.get(f)
            if f == "clinic_count":
                try:
                    val = int(val) if val not in (None, "") else None
                except (ValueError, TypeError):
                    val = None
            doc.__setattr__(f, val)


@api_view(["POST"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_create_api(request):
    """Yeni doktor ekle (doctor_data'ya INSERT)."""
    from .models import Doctor
    from django.utils import timezone

    data = request.data or {}
    name = (data.get("doctor_name") or "").strip()
    if not name:
        return Response({"error": "Имя доктора обязательно."}, status=400)

    doc = Doctor(status=1)
    _doctor_apply_fields(doc, data)
    doc.entry_user = request.user.get_full_name() or request.user.username
    doc.entry_date = timezone.now()

    try:
        doc.save(using="refdb")
    except Exception as exc:
        return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)

    return Response({"id": doc.id, "error": ""})


@api_view(["POST"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_update_api(request):
    """Mevcut doktoru guncelle (id ile, UPDATE)."""
    from .models import Doctor

    data = request.data or {}
    doc_id = data.get("id")
    if not doc_id:
        return Response({"error": "id gerekli."}, status=400)

    try:
        doc = Doctor.objects.using("refdb").get(id=doc_id)
    except Doctor.DoesNotExist:
        return Response({"error": "Доктор не найден."}, status=404)

    _doctor_apply_fields(doc, data)
    doc.entry_user = request.user.get_full_name() or request.user.username

    try:
        doc.save(using="refdb")
    except Exception as exc:
        return Response({"error": f"Ошибка обновления: {exc}"}, status=500)

    return Response({"id": doc.id, "error": ""})


@api_view(["POST"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_delete_api(request):
    """Doktoru sil. Soft delete (status=0) - guvenli, geri alinabilir."""
    from .models import Doctor

    data = request.data or {}
    doc_id = data.get("id")
    if not doc_id:
        return Response({"error": "id gerekli."}, status=400)

    try:
        doc = Doctor.objects.using("refdb").get(id=doc_id)
    except Doctor.DoesNotExist:
        return Response({"error": "Доктор не найден."}, status=404)

    # Soft delete: status=0 (kalici silme yerine - guvenli)
    doc.status = 0
    try:
        doc.save(using="refdb", update_fields=["status"])
    except Exception as exc:
        return Response({"error": f"Ошибка удаления: {exc}"}, status=500)

    return Response({"deleted": doc_id, "error": ""})


@api_view(["GET"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_detail_api(request):
    """Tek doktorun tum alanlari (duzenleme formu icin). ?id=X"""
    from .models import Doctor

    doc_id = request.GET.get("id")
    if not doc_id:
        return Response({"error": "id gerekli."}, status=400)
    try:
        doc = Doctor.objects.using("refdb").get(id=doc_id)
    except Doctor.DoesNotExist:
        return Response({"error": "Доктор не найден."}, status=404)

    out = {"id": doc.id}
    for f in _DOCTOR_WRITABLE:
        out[f] = getattr(doc, f, "") or ""
    return Response(out)


@api_view(["POST"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_geocode_api(request):
    """
    Adres -> koordinat (point_x/y) + adres bilesenleri.
    DaData (birincil) + Yandex (yedek). Provider + anahtarlar GeocodeSettings'ten
    (admin panel) okunur. "Найти адрес" butonu bunu cagirir.
    """
    import os
    import requests
    from .models import GeocodeSettings

    data = request.data or {}
    address = (data.get("address") or "").strip()
    if not address:
        return Response({"error": "Адрес пустой."}, status=400)

    cfg = GeocodeSettings.current()
    provider = (cfg.provider if cfg else "dadata").lower()

    out = {
        "point_x": "", "point_y": "", "full_address": "", "street": "",
        "home_number": "", "city": "", "administrative_area_name": "",
        "sub_administrative_area_name": "", "country_code": "",
        "building_type": "", "error": "",
    }

    try:
        if provider == "yandex":
            out = _geocode_yandex(address, out)
        else:
            out = _geocode_dadata(address, out)
    except Exception as exc:
        return Response({**out, "error": f"Ошибка геокодирования: {exc}"}, status=500)

    return Response(out)


def _geocode_dadata(address, out):
    """DaData clean/address - koordinat + ayristrilmis adres."""
    import os
    import requests
    from .models import GeocodeSettings

    cfg = GeocodeSettings.current()
    key = (cfg.dadata_key if cfg else "") or os.environ.get("DADATA_KEY", "")
    secret = (cfg.dadata_secret if cfg else "") or os.environ.get("DADATA_SECRET", "")
    if not key or not secret:
        out["error"] = "DaData ключ не настроен."
        return out

    resp = requests.post(
        "https://cleaner.dadata.ru/api/v1/clean/address",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Token {key}",
            "X-Secret": secret,
        },
        json=[address],
        timeout=10,
    )
    if resp.status_code != 200:
        out["error"] = f"DaData error {resp.status_code}"
        return out

    arr = resp.json()
    if not arr:
        out["error"] = "Адрес не найден."
        return out
    a = arr[0]

    def g(k):
        v = a.get(k)
        return "" if v is None else str(v)

    out["full_address"] = g("result")
    out["building_type"] = g("house_type_full")
    out["country_code"] = g("country_iso_code")
    out["point_y"] = g("geo_lat")
    out["point_x"] = g("geo_lon")

    region = g("region")
    region_type = g("region_type_full")
    if region_type.lower() == "город":
        out["administrative_area_name"] = region
    else:
        out["administrative_area_name"] = (region + " " + region_type).strip()

    city = g("city")
    if not city:
        out["sub_administrative_area_name"] = region
        out["city"] = region
    else:
        out["sub_administrative_area_name"] = city
        out["city"] = city

    street_type = g("street_type_full")
    street = g("street")
    out["street"] = (street_type + " " + street).strip()
    out["home_number"] = g("house")
    return out


def _geocode_yandex(address, out):
    """Yandex Geocoder - yedek."""
    import os
    import requests
    from .models import GeocodeSettings

    cfg = GeocodeSettings.current()
    key = (cfg.yandex_key if cfg else "") or os.environ.get("YANDEX_GEOCODE_KEY", "")
    if not key:
        out["error"] = "Yandex ключ не настроен."
        return out

    resp = requests.get(
        "https://geocode-maps.yandex.ru/1.x/",
        params={"apikey": key, "format": "json", "geocode": address, "lang": "ru_RU"},
        timeout=10,
    )
    if resp.status_code != 200:
        out["error"] = f"Yandex error {resp.status_code}"
        return out

    j = resp.json()
    try:
        members = j["response"]["GeoObjectCollection"]["featureMember"]
        if not members:
            out["error"] = "Адрес не найден."
            return out
        geo = members[0]["GeoObject"]
        pos = geo["Point"]["pos"].split()
        out["point_x"] = pos[0]
        out["point_y"] = pos[1]
        out["full_address"] = geo.get("metaDataProperty", {}).get(
            "GeocoderMetaData", {}).get("text", "")
    except (KeyError, IndexError):
        out["error"] = "Не удалось разобрать ответ Yandex."
    return out


# PharmacyBase'in yazilabilir alanlari (id haric). pharmacy_detail + bulk_save kullanir.
_PHARMACY_WRITABLE = [
    "country", "area", "region", "city", "city_region", "district", "metro",
    "group_company", "subgroup_company", "pharmacy_no", "pharmacy_address",
    "pharmacy_category", "assortiment", "pharmacy_type", "promo",
    "marketing_staff", "pharmacy_response_person", "pharmacy_tel",
    "pharmacy_email", "pharmacy_activeness", "pharmacy_activation_date",
    "comments", "marketing_staff_no", "pharmacy_number_sale", "found_no",
    "full_address", "requested", "building_type", "country_code",
    "administrative_area_name", "sub_administrative_area_name", "street",
    "homenumber", "point_y", "point_x", "processed", "status", "pharmacy_id",
    "assortiment1", "pharmacy_group", "sku", "cornerNo", "entry_user",
    "pharmacist_name_1", "pharmacy_home_tel", "pharmacist_name_2",
    "pharmacy_work_tel",
]

# Modeldeki IntegerField alanlar — bos string/None -> None, aksi halde int'e cevrilir.
# (PharmacyBase: sku, cornerNo, marketing_staff_no, found_no, processed, status, pharmacy_id)
_PHARMACY_INT_FIELDS = {
    "sku", "cornerNo", "marketing_staff_no", "found_no",
    "processed", "status", "pharmacy_id",
}


def _pharmacy_model(brand):
    """brand -> PharmacySolgar / PharmacyBounty."""
    from .models import PharmacySolgar, PharmacyBounty
    b = (brand or "SOLGAR").upper()
    return PharmacyBounty if "BOUNTY" in b or b == "BN" else PharmacySolgar


def _pharmacy_apply_fields(obj, data):
    for f in _PHARMACY_WRITABLE:
        if f in data:
            val = data.get(f)
            if f in _PHARMACY_INT_FIELDS:
                try:
                    val = int(val) if val not in (None, "") else None
                except (ValueError, TypeError):
                    val = None
            obj.__setattr__(f, val)


@api_view(["POST"])
@permission_classes([HasScreen("PHARMACY")])
def pharmacy_create_api(request):
    """Yeni eczane ekle (brand'e gore tabloya INSERT)."""
    from django.utils import timezone

    data = request.data or {}
    brand = (data.get("brand") or "SOLGAR").strip()
    Model = _pharmacy_model(brand)

    # Номер аптеки artik zorunlu degil (Olga: "не всегда есть").
    obj = Model(status=1)
    _pharmacy_apply_fields(obj, data)
    obj.entry_user = request.user.get_full_name() or request.user.username
    obj.entry_date = timezone.now()

    try:
        obj.save(using="refdb")
    except Exception as exc:
        return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)
    return Response({"id": obj.id, "error": ""})


@api_view(["POST"])
@permission_classes([HasScreen("PHARMACY")])
def pharmacy_update_api(request):
    """Eczaneyi guncelle (brand + id)."""
    data = request.data or {}
    brand = (data.get("brand") or "SOLGAR").strip()
    obj_id = data.get("id")
    if not obj_id:
        return Response({"error": "id gerekli."}, status=400)

    Model = _pharmacy_model(brand)
    try:
        obj = Model.objects.using("refdb").get(id=obj_id)
    except Model.DoesNotExist:
        return Response({"error": "Аптека не найдена."}, status=404)

    _pharmacy_apply_fields(obj, data)
    obj.entry_user = request.user.get_full_name() or request.user.username
    try:
        obj.save(using="refdb")
    except Exception as exc:
        return Response({"error": f"Ошибка обновления: {exc}"}, status=500)
    return Response({"id": obj.id, "error": ""})


@api_view(["POST"])
@permission_classes([HasScreen("PHARMACY")])
def pharmacy_delete_api(request):
    """Eczaneyi sil (soft delete status=0)."""
    data = request.data or {}
    brand = (data.get("brand") or "SOLGAR").strip()
    obj_id = data.get("id")
    if not obj_id:
        return Response({"error": "id gerekli."}, status=400)

    Model = _pharmacy_model(brand)
    try:
        obj = Model.objects.using("refdb").get(id=obj_id)
    except Model.DoesNotExist:
        return Response({"error": "Аптека не найдена."}, status=404)

    obj.status = 0
    try:
        obj.save(using="refdb", update_fields=["status"])
    except Exception as exc:
        return Response({"error": f"Ошибка удаления: {exc}"}, status=500)
    return Response({"deleted": obj_id, "error": ""})


@api_view(["GET"])
@permission_classes([HasScreen("PHARMACY")])
def pharmacy_detail_api(request):
    """Tek eczanenin tum alanlari (duzenleme formu). ?brand=&id="""
    brand = (request.GET.get("brand") or "SOLGAR").strip()
    obj_id = request.GET.get("id")
    if not obj_id:
        return Response({"error": "id gerekli."}, status=400)

    Model = _pharmacy_model(brand)
    try:
        obj = Model.objects.using("refdb").get(id=obj_id)
    except Model.DoesNotExist:
        return Response({"error": "Аптека не найдена."}, status=404)

    out = {"id": obj.id, "brand": brand}
    for f in _PHARMACY_WRITABLE:
        out[f] = getattr(obj, f, "") or ""
    return Response(out)





@api_view(["POST"])
@permission_classes([HasScreen("PHARMACY")])
def pharmacy_bulk_save_api(request):
    """
    Toplu eczane kaydetme (СОХРАНИТЬ). React'te ДОБАВИТЬ ile hazirlanan
    gecici satirlari tek seferde kaydeder. brand'e gore Solgar/Bounty tablosu.

    JSON body: {rows: [{brand, ...eczane1}, {brand, ...eczane2}, ...]}
    Yeni (id yok) -> INSERT, id varsa -> UPDATE.
    """
    from django.utils import timezone
    from django.db import transaction

    data = request.data or {}
    rows = data.get("rows") or []
    if not rows:
        return Response({"error": "Нет строк для сохранения."}, status=400)

    entry_user = request.user.get_full_name() or request.user.username
    now = timezone.now()

    created, updated = 0, 0
    try:
        with transaction.atomic(using="refdb"):
            for r in rows:
                # Номер аптеки artik zorunlu degil (Olga: "не всегда есть") —
                # номер olmayan satirlari da kaydet.
                brand = (r.get("brand") or "SOLGAR").strip()
                Model = _pharmacy_model(brand)

                rid = r.get("id")
                if rid:
                    try:
                        obj = Model.objects.using("refdb").get(id=rid)
                    except Model.DoesNotExist:
                        continue
                    _pharmacy_apply_fields(obj, r)
                    obj.entry_user = entry_user
                    obj.save(using="refdb")
                    updated += 1
                else:
                    obj = Model(status=1)
                    _pharmacy_apply_fields(obj, r)
                    obj.entry_user = entry_user
                    obj.entry_date = now
                    obj.save(using="refdb")
                    created += 1
    except Exception as exc:
        return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)

    return Response({"created": created, "updated": updated, "error": ""})




@api_view(["POST"])
@permission_classes([HasScreen("DOCTOR")])
def doctor_bulk_save_api(request):
    """
    Toplu doktor kaydetme (СОХРАНИТЬ) - React'te ДОБАВИТЬ ile hazirlanan
    gecici satirlari tek seferde doctor_data'ya yazar.

    JSON body: {rows: [{...doktor1}, {...doktor2}, ...]}
    Yeni kayit (id yok) -> INSERT, id varsa -> UPDATE.
    """
    from .models import Doctor
    from django.utils import timezone
    from django.db import transaction

    data = request.data or {}
    rows = data.get("rows") or []
    if not rows:
        return Response({"error": "Нет строк для сохранения."}, status=400)

    entry_user = request.user.get_full_name() or request.user.username
    now = timezone.now()

    created, updated = 0, 0
    try:
        with transaction.atomic(using="refdb"):
            for r in rows:
                name = (r.get("doctor_name") or "").strip()
                if not name:
                    continue

                rid = r.get("id")
                if rid:
                    try:
                        doc = Doctor.objects.using("refdb").get(id=rid)
                    except Doctor.DoesNotExist:
                        continue
                    _doctor_apply_fields(doc, r)
                    doc.entry_user = entry_user
                    doc.save(using="refdb")
                    updated += 1
                else:
                    doc = Doctor(status=1)
                    _doctor_apply_fields(doc, r)
                    doc.entry_user = entry_user
                    doc.entry_date = now
                    doc.save(using="refdb")
                    created += 1
    except Exception as exc:
        return Response({"error": f"Ошибка сохранения: {exc}"}, status=500)

    return Response({"created": created, "updated": updated, "error": ""})    





# ==================== Distributor Report (Storage Stock Observation) ====================
# Java StorageStockObservation + ReportQueries.repStorageStockMonthly'nin
# optimize Python karsiligi. Veri kaynagi: DistributorRecord (depo upload).
# Java 7 report turu istiyor ama DistributorRecord'da region/category/main_group
# yok; mevcut alanlarla 4 anlamli report: DISTRIBUTOR, CITY, ALL_PRODUCTS, BRAND.

# repType -> gruplama alan(lari). operation_type her zaman ilk (STOCK/SALE ayrimi).
_DIST_REPORT_GROUPS = {
    "DISTRIBUTOR_REPORT": ["operation_type", "distributor"],
    "CITY_REPORT": ["operation_type", "city"],
    "ALL_PRODUCTS_REPORT": ["operation_type", "product_name"],
    "BRAND_REPORT": ["operation_type", "brand"],
}

_DIST_REPORT_LABELS = {
    "operation_type": "Тип операции",
    "distributor": "Дистрибьютор",
    "city": "Город",
    "product_name": "Товар",
    "brand": "Бренд",
}

_DIST_REPORT_TYPES = [
    {"value": "DISTRIBUTOR_REPORT", "label": "DISTRIBUTOR_REPORT"},
    {"value": "CITY_REPORT", "label": "CITY_REPORT"},
    {"value": "ALL_PRODUCTS_REPORT", "label": "ALL_PRODUCTS_REPORT"},
    {"value": "BRAND_REPORT", "label": "BRAND_REPORT"},
]


@api_view(["GET"])
@permission_classes([HasScreen("SALES_OBS")])
def distributor_report_api(request):
    """
    Distributor gorumtuleme raporu (Storage Stock Observation).
    run=1 ile DistributorRecord'u filtreleyip gruplar, count+amount toplar.

    Query params:
      run=1, rep_type, operation_type (STOCK/SALE), distributor, city,
      brand (SOLGAR/BOUNTY/OTHER), country, product (product_name),
      begin, end (YYYY-MM-DD)

    Response:
      {options: {rep_types, operations}, report: {columns, rows, total_rows}, error}
    """
    from django.db.models import Sum
    from .models import DistributorRecord

    rep_type = (request.GET.get("rep_type") or "DISTRIBUTOR_REPORT").strip()
    operation_type = (request.GET.get("operation_type") or "").strip().upper()
    distributor = (request.GET.get("distributor") or "").strip()
    city = (request.GET.get("city") or "").strip()
    brand = (request.GET.get("brand") or "").strip()
    country = (request.GET.get("country") or "").strip()
    product = (request.GET.get("product") or "").strip()
    begin = (request.GET.get("begin") or "").strip()
    end = (request.GET.get("end") or "").strip()

    # Kullaniciya gore ulke kilidi (staff disinda kendi ulkesi)
    if not request.user.is_staff:
        uc = (getattr(request.user, "country", "") or "").strip()
        if uc:
            country = uc

    report = None
    error = ""

    if request.GET.get("run"):
        try:
            group = _DIST_REPORT_GROUPS.get(rep_type)
            if not group:
                raise ValueError(f"Bilinmeyen rapor tipi: {rep_type}")

            # Tarih araligi ZORUNLU — legacy stock_sales_table (14M) filtresiz
            # taranmaz. begin+end yoksa bos rapor + bilgi mesaji.
            if not (begin and end):
                return Response({
                    "options": {
                        "rep_types": _DIST_REPORT_TYPES,
                        "operations": [
                            {"value": "STOCK", "label": "STOCK"},
                            {"value": "SALE", "label": "SALES"},
                        ],
                    },
                    "report": {"columns": [], "rows": [], "total_rows": 0},
                    "error": "",
                    "message": "Выберите период (дата с и дата по) для формирования отчёта.",
                })

            # normalize edilmis operation ('STOCK' / 'SALE')
            op = ""
            if operation_type:
                op = "SALE" if operation_type.startswith("SAL") else "STOCK"

            import datetime as _d
            from django.db import connections

            # ---- HAFTALIK pivot: begin'den 7'ser gun, end'e kadar ----
            # Her blok [bstart, bend] (bend dahil). Sutun adi = blogun son gunu
            # (Mon_DD). Son blok kisa olabilir. Resimdeki Java ekranindaki gibi.
            try:
                d_begin = _d.datetime.strptime(begin, "%Y-%m-%d").date()
                d_end = _d.datetime.strptime(end, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Неверный формат даты (YYYY-MM-DD).")
            if d_end < d_begin:
                d_begin, d_end = d_end, d_begin

            _MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            weeks = []  # (label, start_date, end_date_inclusive)
            cur_start = d_begin
            while cur_start <= d_end:
                cur_end = min(cur_start + _d.timedelta(days=6), d_end)
                label = f"{_MON[cur_end.month - 1]}_{cur_end.day:02d}"
                weeks.append((label, cur_start, cur_end))
                cur_start = cur_end + _d.timedelta(days=1)
            n_weeks = len(weeks)

            # grup anahtari -> [count_per_week_list, total]
            combined: dict = {}

            def _add(key, wi, val):
                if key not in combined:
                    combined[key] = [[0] * n_weeks, 0]
                combined[key][0][wi] += int(val or 0)
                combined[key][1] += int(val or 0)

            # ---- yeni platform (DistributorRecord) — haftalara dagit ----
            qs = DistributorRecord.objects.filter(is_confirmed=True)
            if op:
                qs = qs.filter(operation_type=op)
            if distributor:
                qs = qs.filter(distributor=distributor)
            if city:
                qs = qs.filter(city=city)
            if brand:
                qs = qs.filter(brand=brand)
            if country:
                qs = qs.filter(country=country)
            if product:
                qs = qs.filter(product_name=product)
            qs = qs.filter(begin_date__gte=d_begin, begin_date__lte=d_end)

            for rec in qs.values(*group, "begin_date", "count"):
                bd = rec.get("begin_date")
                if not bd:
                    continue
                wi = (bd - d_begin).days // 7
                if wi < 0 or wi >= n_weeks:
                    continue
                key = tuple(rec.get(g, "") or "" for g in group)
                _add(key, wi, rec.get("count") or 0)

            # ---- eski (legacy stock_sales_table) — haftalik CASE pivot ----
            _LEG_COL = {"operation_type": "optype", "distributor": "distributor",
                        "city": "city", "product_name": "product",
                        "brand": "product_type"}
            _b2legacy = {"SOLGAR": "SL", "BOUNTY": "BN", "OTHER": "OS"}
            _legacy2label = {"SL": "SOLGAR", "BN": "BOUNTY", "OS": "OTHER"}
            _op2legacy = {"SALE": "SALES", "STOCK": "STOCK"}

            where = ["rep_begin_date >= %s", "rep_begin_date <= %s"]
            params = [str(d_begin), str(d_end)]
            if op:
                where.append("optype = %s")
                params.append(_op2legacy.get(op, op))
            if distributor:
                where.append("distributor = %s")
                params.append(distributor)
            if city:
                where.append("city = %s")
                params.append(city)
            if brand:
                where.append("product_type = %s")
                params.append(_b2legacy.get(brand, brand))
            if product:
                where.append("product = %s")
                params.append(product)
            # country: stock_sales_table'da yok -> atlanir.

            group_cols = [_LEG_COL[g] for g in group]
            # Her hafta icin bir SUM(CASE ...) sutunu.
            case_cols = []
            case_params = []
            for (_lbl, ws, we) in weeks:
                case_cols.append(
                    "COALESCE(SUM(CASE WHEN rep_begin_date >= %s "
                    "AND rep_begin_date <= %s THEN count ELSE 0 END),0)"
                )
                case_params.extend([str(ws), str(we)])

            sql = (
                f"SELECT {', '.join(group_cols)}, {', '.join(case_cols)} "
                f"FROM solgar_stk.stock_sales_table WHERE {' AND '.join(where)} "
                f"GROUP BY {', '.join(group_cols)}"
            )
            # SQL metninde SELECT (CASE param'lari) WHERE'den once gelir, bu
            # yuzden case_params WHERE params'tan ONCE baglanir.
            full_params = case_params + params
            with connections["refdb"].cursor() as cur:
                cur.execute(sql, full_params)
                for rec in cur.fetchall():
                    key_vals = list(rec[:len(group_cols)])
                    week_vals = list(rec[len(group_cols):])
                    norm = []
                    for g, v in zip(group, key_vals):
                        v = v or ""
                        if g == "operation_type":
                            v = "SALE" if str(v).startswith("SAL") else v
                        elif g == "brand":
                            v = _legacy2label.get(v, v)
                        norm.append(v)
                    key = tuple(norm)
                    for wi, wv in enumerate(week_vals):
                        _add(key, wi, wv)

            # ---- satirlar: grup kolonlari + hafta sutunlari + TOTAL ----
            week_labels = [w[0] for w in weeks]
            columns = ([_DIST_REPORT_LABELS.get(g, g) for g in group]
                       + week_labels + ["TOTAL"])

            week_totals = [0] * n_weeks
            grand_total = 0
            data_rows = []
            for key in sorted(combined.keys(), key=lambda t: tuple(str(x) for x in t)):
                wk, tot = combined[key]
                row = list(key) + [_json_safe(v) for v in wk] + [_json_safe(tot)]
                data_rows.append(row)
                for i in range(n_weeks):
                    week_totals[i] += wk[i]
                grand_total += tot

            # "Total" satiri en uste
            total_row = (["Total"] + [""] * (len(group) - 1)
                         + [_json_safe(v) for v in week_totals]
                         + [_json_safe(grand_total)])
            rows = [total_row] + data_rows

            report = {"columns": columns, "rows": rows, "total_rows": len(rows)}
        except Exception as exc:
            error = f"Ошибка отчета: {exc}"

    return Response({
        "options": {
            "rep_types": _DIST_REPORT_TYPES,
            "operations": [
                {"value": "STOCK", "label": "STOCK"},
                {"value": "SALE", "label": "SALES"},
            ],
        },
        "report": report,
        "error": error,
    })


# Tarih araligi limiti (Hakan): aptek raporlari max 6 ay, distributör max 3 ay.
def _date_range_error(begin: str, end: str, max_months: int):
    """begin/end (YYYY-MM-DD) arasi max_months ayi asarsa Rusca hata mesaji
    doner, yoksa None. Tam max_months kabul, 1 gun fazlasi ret."""
    import datetime as _dd
    try:
        b = _dd.datetime.strptime(begin, "%Y-%m-%d").date()
        e = _dd.datetime.strptime(end, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    if e < b:
        b, e = e, b
    months = (e.year - b.year) * 12 + (e.month - b.month)
    if e.day > b.day:
        months += 1
    if months > max_months:
        return (f"Период не может превышать {max_months} "
                f"{'месяцев' if max_months != 1 else 'месяц'}. "
                f"Выберите диапазон не больше {max_months} мес.")
    return None


# ==================== Chain Sales Report (eczane gorumtuleme - report turleri) ====================
# Java repChainSalesNew'in optimize karsiligi. Veri: SalesRecord (eczane upload).
# Report turleri SalesRecord alanlarina gore (region yok, city var).

# CITY_SALES, SUBGROUP_SALES, MAINGROUP_SALES kaldirildi.
# MEDREP_SALES -> ADRES_SALES (ayni salesreader kolonu; adres metni).
_CHAIN_REPORT_GROUPS = {
    "CHAIN_SALES": ["chain_name"],
    "PRODUCT_SALES": ["product_name"],
    "ADRES_SALES": ["salesreader"],
    "BRAND_SALES": ["brand"],
}

_CHAIN_REPORT_LABELS = {
    "chain_name": "Аптечная сеть",
    "city": "Город",
    "product_name": "Товар",
    "salesreader": "Адрес",
    "brand": "Бренд",
    "subgroup": "Подгруппа",
    "main_group": "Основная группа",
}

_CHAIN_REPORT_TYPES = [
    {"value": "CHAIN_SALES", "label": "CHAIN_SALES"},
    {"value": "PRODUCT_SALES", "label": "PRODUCT_SALES"},
    {"value": "ADRES_SALES", "label": "ADRES_SALES"},
    {"value": "BRAND_SALES", "label": "BRAND_SALES"},
]


@api_view(["GET"])
@permission_classes([HasScreen("CHAIN_REPORT")])
def chain_sales_report_api(request):
    """
    Eczane (aptechnoy seti) gorumtuleme raporu - report turleri.
    run=1 ile SalesRecord'u filtreleyip gruplar, count+amount toplar.

    Query params:
      run=1, rep_type, brand (SOLGAR/BOUNTY/OTHER), country, chain (chain_name),
      city, product (product_name), medrep (salesreader), begin, end (YYYY-MM-DD)

    Response:
      {options: {rep_types, brands}, report: {columns, rows, total_rows}, error}
    """
    from django.db.models import Sum
    from .models import SalesRecord

    rep_type = (request.GET.get("rep_type") or "CHAIN_SALES").strip()
    brand = (request.GET.get("brand") or "").strip()
    country = (request.GET.get("country") or "").strip()
    chain = (request.GET.get("chain") or "").strip()
    city = (request.GET.get("city") or "").strip()
    product = (request.GET.get("product") or "").strip()
    medrep = (request.GET.get("medrep") or "").strip()
    begin = (request.GET.get("begin") or "").strip()
    end = (request.GET.get("end") or "").strip()

    if not request.user.is_staff:
        uc = (getattr(request.user, "country", "") or "").strip()
        if uc:
            country = uc

    report = None
    error = ""

    if request.GET.get("run"):
        try:
            group = _CHAIN_REPORT_GROUPS.get(rep_type)
            if not group:
                raise ValueError(f"Bilinmeyen rapor tipi: {rep_type}")

            # Tarih araligi limiti: aptek raporlari max 6 ay.
            _rng_err = _date_range_error(begin, end, 6)
            if _rng_err:
                return Response({
                    "options": {
                        "rep_types": _CHAIN_REPORT_TYPES,
                        "brands": [
                            {"value": "SOLGAR", "label": "SOLGAR"},
                            {"value": "BOUNTY", "label": "NATURES BOUNTY"},
                            {"value": "OTHER", "label": "OTHER"},
                        ],
                    },
                    "report": None, "error": _rng_err,
                })

            # Tarih araligi ZORUNLU — legacy sales_pharmacy (45M) filtresiz
            # taranmaz. begin+end yoksa bos rapor + bilgi mesaji.
            if not (begin and end):
                report = {"columns": [], "rows": [], "total_rows": 0}
                return Response({
                    "options": {
                        "rep_types": _CHAIN_REPORT_TYPES,
                        "brands": [
                            {"value": "SOLGAR", "label": "SOLGAR"},
                            {"value": "BOUNTY", "label": "NATURES BOUNTY"},
                            {"value": "OTHER", "label": "OTHER"},
                        ],
                    },
                    "report": report,
                    "error": "",
                    "message": "Выберите период (дата с и дата по) для формирования отчёта.",
                })

            # ---- yeni platform verisi (sales_record) ----
            qs = SalesRecord.objects.filter(is_confirmed=True)
            if brand:
                qs = qs.filter(brand=brand)
            if country:
                qs = qs.filter(country=country)
            if chain:
                qs = qs.filter(chain_name=chain)
            if city:
                qs = qs.filter(city=city)
            if product:
                qs = qs.filter(product_name=product)
            if medrep:
                qs = qs.filter(salesreader=medrep)
            if begin:
                qs = qs.filter(report_date__gte=begin)
            if end:
                qs = qs.filter(report_date__lte=end)

            agg = (
                qs.values(*group)
                .annotate(total_count=Sum("count"), total_amount=Sum("amount"))
                .order_by(*group)
            )

            # grup anahtari -> [count, amount] birikimli sozluk
            combined: dict = {}
            for r in agg:
                key = tuple(r.get(g, "") or "" for g in group)
                combined.setdefault(key, [0, 0])
                combined[key][0] += int(r.get("total_count") or 0)
                combined[key][1] += r.get("total_amount") or 0

            # ---- eski (legacy sales_pharmacy) verisi ----
            # Sadece legacy'de net karsiligi olan rapor tiplerine eklenir.
            # SUBGROUP/MAINGROUP legacy'de urun grubu DEGIL (zincir adi), bu
            # yuzden onlar sadece sales_record'dan gelir.
            _LEGACY_GROUP_COL = {
                "CHAIN_SALES": "main_group",
                "PRODUCT_SALES": "product_Name",
                "ADRES_SALES": "sales_reader",
                "BRAND_SALES": "product_type",
            }
            legacy_col = _LEGACY_GROUP_COL.get(rep_type)
            if legacy_col:
                from django.db import connections
                import datetime as _d
                # brand: API SOLGAR/BOUNTY -> legacy SL/BN
                _b2legacy = {"SOLGAR": "SL", "BOUNTY": "BN", "OTHER": "OB"}
                _legacy2label = {"SL": "SOLGAR", "BN": "BOUNTY", "OB": "OTHER"}

                where = ["sales_date >= %s", "sales_date < %s"]
                # end'i gun-sonu dahil et (ertesi gun, exclusive)
                try:
                    end_dt = _d.datetime.strptime(end, "%Y-%m-%d") + _d.timedelta(days=1)
                    end_x = end_dt.strftime("%Y-%m-%d")
                except ValueError:
                    end_x = end
                params = [begin, end_x]
                if brand:
                    where.append("product_type = %s")
                    params.append(_b2legacy.get(brand, brand))
                if country:
                    where.append("country = %s")
                    params.append(country)
                if chain:
                    where.append("main_group = %s")
                    params.append(chain)
                if city:
                    where.append("city = %s")
                    params.append(city)
                if product:
                    where.append("product_Name = %s")
                    params.append(product)
                if medrep:
                    where.append("sales_reader = %s")
                    params.append(medrep)

                sql = (
                    f"SELECT {legacy_col} AS k, "
                    "COALESCE(SUM(sales_count),0), "
                    "COALESCE(SUM(CAST(sales_amount AS DECIMAL(14,2))),0) "
                    f"FROM solgar_tst.sales_pharmacy WHERE {' AND '.join(where)} "
                    f"GROUP BY {legacy_col}"
                )
                with connections["refdb"].cursor() as cur:
                    cur.execute(sql, params)
                    for k, cnt, amt in cur.fetchall():
                        # BRAND_SALES: legacy kodu (SL/BN) -> etiket (SOLGAR/BOUNTY)
                        if rep_type == "BRAND_SALES":
                            k = _legacy2label.get(k, k or "")
                        key = (k or "",)
                        combined.setdefault(key, [0, 0])
                        combined[key][0] += int(cnt or 0)
                        combined[key][1] += amt or 0

            # ---- birlesik sonucu satirlara dok ----
            columns = [_CHAIN_REPORT_LABELS.get(g, g) for g in group] + ["Кол-во", "Сумма"]
            rows = []
            for key in sorted(combined.keys(), key=lambda t: tuple(str(x) for x in t)):
                row = list(key)
                row.append(_json_safe(combined[key][0]))
                row.append(_json_safe(combined[key][1]))
                rows.append(row)

            report = {"columns": columns, "rows": rows, "total_rows": len(rows)}
        except Exception as exc:
            error = f"Ошибка отчета: {exc}"

    return Response({
        "options": {
            "rep_types": _CHAIN_REPORT_TYPES,
            "brands": [
                {"value": "SOLGAR", "label": "SOLGAR"},
                {"value": "BOUNTY", "label": "NATURES BOUNTY"},
                {"value": "OTHER", "label": "OTHER"},
            ],
        },
        "report": report,
        "error": error,
    })
