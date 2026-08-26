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
