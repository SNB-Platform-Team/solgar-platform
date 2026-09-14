"""
sales app — business logic for parsing and classifying chain sales files.

The parser reads a chain Excel export, locates the header row by column
names, extracts each product line, and classifies it as Solgar or Bounty
by inspecting the product name. This mirrors the logic of the legacy
desktop parser but is written for openpyxl.
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from openpyxl import load_workbook

from .models import SalesRecord

# Keywords that classify a product by its name (case-insensitive).
SOLGAR_KEYWORDS = ("солгар", "solgar", "Solgar", "SOLGAR", "Solgar vitamin") #if there's no any key, then return Solgar

@dataclass
class ParsedRow:
    """One parsed product line, before saving."""

    product_name: str
    brand: str
    pharmacy: str
    city: str
    count: int
    amount: Decimal
    remaining_count: int
    remaining_amount: Decimal

@dataclass
class ParseResult:
    """Outcome of parsing a file: rows plus computed totals."""

    rows: list[ParsedRow] = field(default_factory=list)
    solgar_count: int = 0
    solgar_amount: Decimal = Decimal("0")
    bounty_count: int = 0
    bounty_amount: Decimal = Decimal("0")
    product_types: int = 0

    @property
    def total_rows(self) -> int:
        """Number of parsed rows."""
        return len(self.rows)     

class SalesParseError(Exception):
    """Raised when a file cannot be parsed (e.g. header not found)."""
#admin panelden
class ChainParser:                                                      
    """
    Single parametric parser for all chains/distributors.

    Instead of one parser per chain, this reads a ChainDefinition (column 
    mapping, orientation, country) and parses accordingly. Adding a chain
    means adding a ChainDefinition row, not new code.
    """

    def __init__(self, definition) -> None:
        """
        Args:
            definition: A ChainDefinition instance describing this chain.
        """
        self.definition = definition
        self.column_map = definition.column_map or {}

    def classify(self, product_name: str) -> str:
        """
        Classify a product by its name using the active BrandDefinition
        records. Active brands are checked in priority order; the first
        whose keyword appears in the name wins. If none match, the default
        brand is used. Fully parametric — no brand is hard-coded.
        """
        name = product_name.lower()
        for apo in ("’", "‘", "`", "'"):
            name = name.replace(apo, "")

        brands = self._active_brands()

        default_code = SalesRecord.Brand.SOLGAR  # fallback if no default set
        for brand in brands:
            if brand.is_default:
                default_code = brand.code
            for kw in brand.keywords:
                if kw and str(kw).lower() in name:
                    return brand.code

        return default_code

    def _active_brands(self):
        """
        Return active brand definitions in priority order, cached on the
        instance so we hit the database once per file, not once per row.
        """
        if not hasattr(self, "_brands_cache"):
            from .models import BrandDefinition

            self._brands_cache = list(
                BrandDefinition.objects.filter(is_active=True).order_by("priority", "name")
            )
        return self._brands_cache

    def _to_int(self, value) -> int:
        """Best-effort convert a cell value to int; 0 on failure."""
        if value is None or value == "":
            return 0
        try:
            s = str(value).replace(",", ".").strip()
            return int(float(s))
        except (ValueError, TypeError):
            return 0

    def _to_decimal(self, value) -> Decimal:
        """Best-effort convert a cell value to Decimal; 0 on failure."""
        if value is None or value == "":
            return Decimal("0")
        try:
            s = str(value).replace(",", ".").strip()
            return Decimal(s).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    def _read_sheet(self, file_obj, filename: str = "") -> list[list]:
        
        name = (filename or getattr(file_obj, "name", "")).lower()

        if name.endswith(".xls"): 
            try:
                import xlrd

                file_obj.seek(0)
                data = file_obj.read()
                book = xlrd.open_workbook(file_contents=data)
                sheet = book.sheet_by_index(0)
                return [
                    [sheet.cell_value(r, c) for c in range(sheet.ncols)]
                    for r in range(sheet.nrows)
                ]
            except ImportError as exc:
                raise SalesParseError("Для чтения .xls требуется xlrd.") from exc
            except Exception as exc:
                raise SalesParseError(f"Не удалось открыть .xls: {exc}") from exc
        else:
            try:
                file_obj.seek(0)
                wb = load_workbook(file_obj, data_only=True, read_only=True)
            except Exception as exc:
                raise SalesParseError(f"Не удалось открыть файл: {exc}") from exc
            ws = wb.active
            return [list(row) for row in ws.iter_rows(values_only=True)]

    def _find_header(self, rows: list[list]) -> tuple[int, dict[str, int]]:
        """
        Locate the header row and map logical fields to column indexes,
        using this chain's column_map. The 'product' field is mandatory.
        """
        # Lowercased target header text for each logical field.
        wanted = {
            field: str(header).strip().lower()
            for field, header in self.column_map.items()
        }
        limit = self.definition.header_search_limit or 30

        for row_idx in range(min(len(rows), limit)):
            found: dict[str, int] = {}
            for col_idx, value in enumerate(rows[row_idx]):
                if value is None:
                    continue
                cell_text = str(value).strip().lower()
                for field, header in wanted.items():
                    if cell_text == header:
                        found[field] = col_idx
            if "product" in found:
                return row_idx, found

        product_header = self.column_map.get("product", "?")
        raise SalesParseError(
            f"Не удалось найти заголовок «{product_header}» в файле."
        )

    def parse(self, file_obj, filename: str = "") -> "ParseResult":
        """
        Parse a file into a ParseResult using this chain's definition.

        Currently supports vertical layout; horizontal can be added later
        by branching on self.definition.orientation.
        """
        rows = self._read_sheet(file_obj, filename)
        if not rows:
            return ParseResult()

        header_row, cols = self._find_header(rows)

        result = ParseResult()
        seen_products: set[str] = set()

        for row_idx in range(header_row + 1, len(rows)):
            row = rows[row_idx]

            def cell(field: str):
                col = cols.get(field)
                if col is None or col >= len(row):
                    return None
                return row[col]

            product = cell("product")
            if product is None or str(product).strip() == "":
                continue
            product_name = str(product).strip()

            brand = self.classify(product_name)
            count = self._to_int(cell("count"))
            amount = self._to_decimal(cell("amount"))
            remaining_count = self._to_int(cell("remaining_count"))
            pharmacy = str(cell("pharmacy") or "").strip()
            city = str(cell("city") or "").strip()

            parsed = ParsedRow(
                product_name=product_name,
                brand=brand,
                pharmacy=pharmacy,
                city=city,
                count=count,
                amount=amount,
                remaining_count=remaining_count,
                remaining_amount=Decimal("0"),
            )
            result.rows.append(parsed)
            seen_products.add(product_name)

            if brand == SalesRecord.Brand.SOLGAR:
                result.solgar_count += count
                result.solgar_amount += amount
            elif brand == SalesRecord.Brand.BOUNTY:
                result.bounty_count += count
                result.bounty_amount += amount

        result.product_types = len(seen_products)
        return result

class SalesUploadService:
    """Business operations for uploading and saving sales data."""

    def __init__(self) -> None:
        """Wire up dependencies."""
        from .repositories import SalesRepository

        self.repository = SalesRepository()

    def preview(self, file_obj, chain_definition, filename: str = "") -> ParseResult:
        """Parse a file using a chain definition and return the result."""
        parser = ChainParser(chain_definition)
        return parser.parse(file_obj, filename)

    def save_records(
        self, parse_result: ParseResult, report_date, chain_name: str,
        country: str, user,
    ) -> int:
        """
        Persist parsed rows as SalesRecord objects.

        Args:
            parse_result: The parsed rows to save.
            report_date: The report date for these records.
            chain_name: The chain these records belong to.
            country: The country.
            user: The uploading user.

        Returns:
            The number of records created.
        """
        records = [
            SalesRecord(
                report_date=report_date,
                chain_name=chain_name,
                country=country,
                product_name=row.product_name,
                brand=row.brand,
                pharmacy=row.pharmacy,
                city=row.city,
                count=row.count,
                amount=row.amount,
                remaining_count=row.remaining_count,
                remaining_amount=row.remaining_amount,
                uploaded_by=user,
            )
            for row in parse_result.rows
        ]
        return self.repository.bulk_create(records)

class SalesViewService:
    """Business operations for viewing and aggregating saved sales data."""

    def __init__(self) -> None:
        """Wire up the repository."""
        from .repositories import SalesRepository

        self.repository = SalesRepository()

    def export_to_excel(self, **filters):
        """
        Build an .xlsx workbook of the filtered sales records.

        Returns:
            An openpyxl Workbook ready to be streamed to the client.
        """
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        records = self.repository.filter_records(**filters)

        wb = Workbook()
        ws = wb.active
        ws.title = "Продажи"

        headers = [
            "Бренд", "Товар", "Сеть", "Дата", "Страна",
            "Город", "Аптека", "Кол-во", "Сумма", "Остаток",
        ]
        ws.append(headers)

        # Header styling.
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="1F4E79")
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill

        # Data rows.
        for rec in records.iterator():
            ws.append([
                rec.get_brand_display(),
                rec.product_name,
                rec.chain_name,
                rec.report_date.strftime("%d.%m.%Y") if rec.report_date else "",
                rec.country,
                rec.city,
                rec.pharmacy,
                rec.count,
                float(rec.amount),
                rec.remaining_count,
            ])

        # Reasonable column widths.
        widths = [16, 45, 12, 12, 14, 18, 30, 10, 12, 10]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[chr(64 + i)].width = w

        return wb

    def query(self, **filters) -> dict:
        """
        Run a filtered query and compute brand totals.

        Returns a dict with the records and aggregated totals.
        """
        from django.db.models import Sum

        records = self.repository.filter_records(**filters)

        solgar = records.filter(brand=SalesRecord.Brand.SOLGAR).aggregate(
            c=Sum("count"), a=Sum("amount")
        )
        bounty = records.filter(brand=SalesRecord.Brand.BOUNTY).aggregate(
            c=Sum("count"), a=Sum("amount")
        )

        return {
            "records": records,
            "total_rows": records.count(),
            "solgar_count": solgar["c"] or 0,
            "solgar_amount": solgar["a"] or 0,
            "bounty_count": bounty["c"] or 0,
            "bounty_amount": bounty["a"] or 0,
        }

    #bu
    def filter_options(self, country: str = "") -> dict:
        """Return distinct values for the filter dropdowns."""
        options = {
            "report_dates": self.repository.distinct_report_dates(),
            "chains": self.repository.distinct_chains(country=country),
        }
        options.update(self.repository.group_options(country=country))
        return options

    def chain_report(self, main_group="", sub_group="", region="", district="", **filters) -> dict:
        """
        Date-range chain-sales query with brand totals, plus optional
        product-category and geographic filters resolved via reference data.
        """
        from django.db.models import Sum

        records = self.repository.filter_by_range(**filters)

        # Product category filter: match sales product_name against ProductGroup.
        if main_group or sub_group:
            keys = self.repository.product_names_for_group(main_group, sub_group)
            # Match case-insensitively: annotate lower(product_name) in Python-safe way.
            from django.db.models.functions import Lower
            records = records.annotate(pn_lower=Lower("product_name")).filter(pn_lower__in=keys)

        # Geographic filter: match sales city against AddressGroup.
        # Sales cities carry settlement suffixes (" г", " с", " пгт"...) that
        # reference cities lack, so we strip them before matching.
        if region or district:
            city_keys = self.repository.cities_for_region(region, district)
            id_city = list(
                SalesRecord.objects.filter(id__in=records.values("id")).values_list("id", "city")
            )
            matching_ids = [
                rid for rid, city in id_city
                if self._normalize_city(city) in city_keys
            ]
            records = records.filter(id__in=matching_ids)

        solgar = records.filter(brand=SalesRecord.Brand.SOLGAR).aggregate(
            c=Sum("count"), a=Sum("amount")
        )
        bounty = records.filter(brand=SalesRecord.Brand.BOUNTY).aggregate(
            c=Sum("count"), a=Sum("amount")
        )
        return {
            "records": records,
            "total_rows": records.count(),
            "solgar_count": solgar["c"] or 0,
            "solgar_amount": solgar["a"] or 0,
            "bounty_count": bounty["c"] or 0,
            "bounty_amount": bounty["a"] or 0,
        }

        return {
            "records": records,
            "total_rows": records.count(),
            "solgar_count": solgar["c"] or 0,
            "solgar_amount": solgar["a"] or 0,
            "bounty_count": bounty["c"] or 0,
            "bounty_amount": bounty["a"] or 0,
        }

    @staticmethod
    def _normalize_city(city: str) -> str:
        """
        Normalize a sales city name for matching against reference data:
        lowercase and strip trailing settlement-type suffixes.
        """
        if not city:
            return ""
        name = city.lower().strip()
        # Remove common trailing settlement markers.
        for suffix in (" г", " с", " пгт", " д", " п", " рп", " ст", " х"):
            if name.endswith(suffix):
                name = name[: -len(suffix)].strip()
                break
        return name

class DistributorUploadService:
    """Upload and save distributor sales/stock data (parametric parser)."""

    def preview(self, file_obj, chain_definition, filename: str = "") -> ParseResult:
        """Parse a distributor file using its chain definition."""
        parser = ChainParser(chain_definition)
        return parser.parse(file_obj, filename)

    def save_records(
        self, parse_result: ParseResult, distributor: str, operation_type: str,
        country: str, begin_date, end_date, user,
    ) -> int:
        """Persist parsed rows as DistributorRecord objects."""
        from .models import DistributorRecord

        records = [
            DistributorRecord(
                distributor=distributor,
                operation_type=operation_type,
                country=country,
                begin_date=begin_date,
                end_date=end_date,
                product_name=row.product_name,
                brand=row.brand,
                count=row.count,
                amount=row.amount,
                city=row.city,
                client=row.pharmacy,  # parser's 'pharmacy' field maps to client
            )
            for row in parse_result.rows
        ]
        for rec in records:
            rec.uploaded_by = user
        DistributorRecord.objects.bulk_create(records)
        return len(records)

class DistributorViewService:
    """View and aggregate saved distributor records."""

    def __init__(self) -> None:
        """Wire up the repository."""
        from .repositories import DistributorRepository
        #python manage.py runserver

        self.repository = DistributorRepository()

    def query(self, **filters) -> dict:
        """Filtered query with Solgar/Bounty totals."""
        from django.db.models import Sum
        from .models import DistributorRecord

        records = self.repository.filter_records(**filters)
        solgar = records.filter(brand=DistributorRecord.Brand.SOLGAR).aggregate(
            c=Sum("count"), a=Sum("amount")
           # c=sum("count"), a=sum("amount")
        )
        bounty = records.filter(brand=DistributorRecord.Brand.BOUNTY).aggregate(
            c=Sum("count"), a=Sum("amount")
        )
        return {
            "records": records,
            "total_rows": records.count(),
            "solgar_count": solgar["c"] or 0,
            "solgar_amount": solgar["a"] or 0,
            "bounty_count": bounty["c"] or 0,
            "bounty_amount": bounty["a"] or 0,
            
        }

    def filter_options(self) -> dict:
        """Distinct values for filter dropdowns."""
        return {"distributors": self.repository.distinct_distributors()}


class DoctorViewService:
    """
    Read/query service for the Doctor Entry & Update screen.

    Wraps DoctorRepository for cascading options and provides the filtered
    doctor list behind the Java 'List Doctor' (Список врачей) button.
    """

    def __init__(self):
        from .repositories import DoctorRepository

        self.repository = DoctorRepository()

    def address_options(self, country: str = "", area: str = "", region: str = "") -> dict:
        """Bundle all cascading dropdown options for the initial page load."""
        return {
            "countries": self.repository.countries(),
            "areas": self.repository.areas(country=country),
            "regions": self.repository.regions(country=country, area=area),
            "cities": self.repository.cities(country=country, area=area, region=region),
            "districts": self.repository.districts(country=country, area=area, region=region),
            "medreps": self.repository.medreps(),
            "specialties": self.repository.specialties(),
            "unified_specialties": self.repository.unified_specialties(),
        }

    PAGE_SIZE = 200

    def _paginate(self, qs, page, total):
        """Slice the queryset to the requested page and return a result dict."""
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1
        size = self.PAGE_SIZE
        start = (page - 1) * size
        records = list(qs[start:start + size])
        num_pages = max(1, (total + size - 1) // size)
        return {
            "records": records,
            "total_rows": total,
            "page": page,
            "num_pages": num_pages,
            "page_size": size,
            "has_prev": page > 1,
            "has_next": page < num_pages,
        }

    def _paged_count_doctor(self, qs, has_filter):
        """Total doctor count; cache the unfiltered count for 5 minutes."""
        if has_filter:
            return qs.count()
        from django.core.cache import cache
        total = cache.get("doctor_total")
        if total is None:
            total = qs.count()
            cache.set("doctor_total", total, 300)
        return total

    def query(
        self,
        brand: str = "", country: str = "", area: str = "", region: str = "",
        city: str = "", medrep: str = "", specialty: str = "",
        unified_specialty: str = "", category: str = "", activeness: str = "",
        doctor_name: str = "", clinic_status: str = "", search: str = "",
        page: int = 1,
    ) -> dict:
        """
        Return doctor rows matching the given filters (all optional, empty
        ignored). Mirrors the Java getDoctorInfo query. Only active rows
        (status=1) are listed.
        """
        from .models import Doctor

        qs = Doctor.objects.filter(status=1)

        if brand:
            qs = qs.filter(brand=brand)
        if country:
            qs = qs.filter(country=country)
        if area:
            qs = qs.filter(area=area)
        if region:
            qs = qs.filter(region=region)
        if city:
            qs = qs.filter(city=city)
        if medrep:
            qs = qs.filter(medrep=medrep)
        if specialty:
            qs = qs.filter(specialty=specialty)
        if unified_specialty:
            qs = qs.filter(unified_specialty=unified_specialty)
        if category:
            qs = qs.filter(category=category)
        if activeness:
            qs = qs.filter(activeness=activeness)
        if doctor_name:
            qs = qs.filter(doctor_name__icontains=doctor_name)
        if clinic_status:
            qs = qs.filter(clinic_status=clinic_status)

        # Genis arama: isim + sehir + klinik (tek kutu)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(doctor_name__icontains=search)
                | Q(city__icontains=search)
                | Q(clinic_name__icontains=search)
            )

        qs = qs.order_by("country", "area", "region", "city", "doctor_name")

        has_filter = any([
            brand, country, area, region, city, medrep, specialty,
            unified_specialty, category, activeness, doctor_name,
            clinic_status, search,
        ])
        total = self._paged_count_doctor(qs, has_filter)
        return self._paginate(qs, page, total)


class DoctorWriteService:
    """
    Create / update / soft-delete service for the Doctor screen.

    Web-native: each action hits the DB immediately (no client-side batch
    like the Java JTable). Deletes are soft (status=0), matching the Java
    behaviour where a deleted row is flagged rather than physically removed.
    """

    EDITABLE_FIELDS = (
        "brand", "country", "area", "region", "district", "city",
        "activeness", "medrep", "doctor_date", "doctor_name",
        "unified_specialty", "specialty", "position_regalia", "category",
        "clinic_name", "clinic_name1", "clinic_status", "clinic_address",
        "clinic_count", "key_person", "doctor_tel", "doctor_email",
        "full_address", "building_type", "country_code",
        "administrative_area_name", "sub_administrative_area_name",
        "street", "homenumber", "point_y", "point_x",
    )

    def _clean(self, data: dict) -> dict:
        """Keep only known fields; coerce clinic_count to int or None."""
        cleaned = {}
        for f in self.EDITABLE_FIELDS:
            if f in data:
                cleaned[f] = data[f]
        if "clinic_count" in cleaned:
            raw = str(cleaned["clinic_count"]).strip()
            cleaned["clinic_count"] = int(raw) if raw.isdigit() else None
        return cleaned

    def create(self, data: dict, user_name: str = ""):
        """Insert a new doctor row (status=1)."""
        from django.utils import timezone

        from .models import Doctor

        fields = self._clean(data)
        fields["status"] = 1
        fields["entry_user"] = user_name
        fields["entry_date"] = timezone.now()
        return Doctor.objects.create(**fields)

    def update(self, doctor_id: int, data: dict, user_name: str = "") -> int:
        """Update an existing doctor row. Returns number of rows updated."""
        from django.utils import timezone

        from .models import Doctor

        fields = self._clean(data)
        fields["entry_user"] = user_name
        fields["entry_date"] = timezone.now()
        return Doctor.objects.filter(pk=doctor_id).update(**fields)

    def soft_delete(self, doctor_id: int) -> int:
        """Soft-delete: flag status=0 so the row drops out of the active list."""
        from .models import Doctor

        return Doctor.objects.filter(pk=doctor_id).update(status=0)


class PharmacyValidationError(Exception):
    """Raised when a pharmacy record fails a business rule (e.g. corner)."""


class PharmacyViewService:
    """
    Read/query service for the Pharmacy Entry & Update screen.

    Brand drives everything: the Java screen picks the company (SOLGAR /
    NATURES BOUNTY / OBF) first, then every other dropdown and the list are
    loaded for that brand's table. So `brand` is threaded through all calls.
    """

    def __init__(self):
        from .repositories import PharmacyRepository

        self.repository = PharmacyRepository()

    def dropdown_options(self, brand: str = "", country: str = "", area: str = "",
                         region: str = "", city: str = "") -> dict:
        """All dropdown lists for the initial page load, for one brand."""
        r = self.repository
        return {
            "countries": r.countries(brand),
            "areas": r.areas(brand, country=country),
            "regions": r.regions(brand, country=country, area=area),
            "cities": r.cities(brand, country=country, area=area, region=region),
            "metros": r.metros(brand, city=city),
            "districts": r.districts(brand, country=country, area=area, region=region),
            "chains": r.chains(brand),
            "subchains": r.subchains(brand),
            "pharmacy_categories": r.pharmacy_categories(brand),
            "pharmacy_types": r.pharmacy_types(brand),
            "promos": r.promos(brand),
            "assortiments": r.assortiments(brand),
            "pharmacy_groups": r.pharmacy_groups(brand),
            "marketing_staff": r.marketing_staff(brand),
        }

    PAGE_SIZE = 200

    def _paginate(self, qs, page, total):
        """Slice the queryset to the requested page and return a result dict."""
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1
        size = self.PAGE_SIZE
        start = (page - 1) * size
        records = list(qs[start:start + size])
        num_pages = max(1, (total + size - 1) // size)
        return {
            "records": records,
            "total_rows": total,
            "page": page,
            "num_pages": num_pages,
            "page_size": size,
            "has_prev": page > 1,
            "has_next": page < num_pages,
        }

    def _paged_count(self, qs, model, has_filter, brand):
        """
        Total row count for pagination. Filtered results are counted directly
        (cheap, small). The unfiltered full-table count is cached for 5 minutes
        so that many concurrent users don't each scan the whole table.
        """
        if has_filter:
            return qs.count()
        from django.core.cache import cache
        key = f"pharm_total_{model.__name__}_{brand}"
        total = cache.get(key)
        if total is None:
            total = qs.count()
            cache.set(key, total, 300)  # 5 dk
        return total

    def query(self, brand: str = "", country: str = "", area: str = "", region: str = "",
              city: str = "", group_company: str = "", subgroup_company: str = "",
              pharmacy_category: str = "", pharmacy_type: str = "", promo: str = "",
              marketing_staff: str = "", pharmacy_activeness: str = "",
              pharmacy_address: str = "", search: str = "",
              page: int = 1) -> dict:
        """
        Return pharmacy rows for a brand matching the filters (empty ignored).
        Mirrors the Java getPharmInfo query. Only active rows (status=1).
        """
        model = self.repository._model_for(brand)
        qs = model.objects.filter(status=1)

        if country:
            qs = qs.filter(country=country)
        if area:
            qs = qs.filter(area=area)
        if region:
            qs = qs.filter(region=region)
        if city:
            qs = qs.filter(city=city)
        if group_company:
            qs = qs.filter(group_company=group_company)
        if subgroup_company:
            qs = qs.filter(subgroup_company=subgroup_company)
        if pharmacy_category:
            qs = qs.filter(pharmacy_category=pharmacy_category)
        if pharmacy_type:
            qs = qs.filter(pharmacy_type=pharmacy_type)
        if promo:
            qs = qs.filter(promo=promo)
        if marketing_staff:
            qs = qs.filter(marketing_staff=marketing_staff)
        if pharmacy_activeness:
            qs = qs.filter(pharmacy_activeness=pharmacy_activeness)
        if pharmacy_address:
            qs = qs.filter(pharmacy_address__icontains=pharmacy_address)

        # Genis arama: isim + sehir + adres (tek kutu, cok-kullanici dostu)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(pharmacy_name__icontains=search)
                | Q(city__icontains=search)
                | Q(pharmacy_address__icontains=search)
            )

        qs = qs.order_by("country", "area", "region", "city", "group_company")

        # --- Sayfalama (200/sayfa) + dengeli sayim ---
        # Filtre/arama varsa sonuc kucuk -> count ucuz.
        # Filtresiz ham liste -> toplam sayiyi cache'le (5 dk), boylece 500
        # kullanici her acilista 77K saymaz.
        has_filter = any([
            country, area, region, city, group_company, subgroup_company,
            pharmacy_category, pharmacy_type, promo, marketing_staff,
            pharmacy_activeness, pharmacy_address, search,
        ])
        total = self._paged_count(qs, model, has_filter, brand)
        return self._paginate(qs, page, total)


class PharmacyWriteService:
    """
    Create / update / soft-delete for pharmacies. Writes go to the brand's
    table (Solgar/OBF -> solgar, Bounty -> bounty). Web-native: each action
    hits the DB immediately. Deletes are soft (status=0).
    """

    EDITABLE_FIELDS = (
        "country", "area", "region", "city", "city_region", "district", "metro",
        "group_company", "subgroup_company", "pharmacy_no", "pharmacy_address",
        "pharmacy_category", "assortiment", "pharmacy_type", "promo",
        "marketing_staff", "pharmacy_response_person", "pharmacy_tel",
        "pharmacy_email", "pharmacy_activeness", "pharmacy_activation_date",
        "comments", "pharmacy_number_sale",
        "full_address", "building_type", "country_code",
        "administrative_area_name", "sub_administrative_area_name",
        "street", "homenumber", "point_y", "point_x",
        "assortiment1", "pharmacy_group",
        "pharmacist_name_1", "pharmacy_home_tel",
        "pharmacist_name_2", "pharmacy_work_tel",
    )
    INT_FIELDS = ("marketing_staff_no", "found_no", "sku", "cornerNo", "pharmacy_id")

    def __init__(self):
        from .repositories import PharmacyRepository

        self.repository = PharmacyRepository()

    def _clean(self, data: dict) -> dict:
        """Keep known fields; coerce int fields."""
        cleaned = {}
        for f in self.EDITABLE_FIELDS:
            if f in data:
                cleaned[f] = data[f]
        for f in self.INT_FIELDS:
            if f in data:
                raw = str(data.get(f, "")).strip()
                cleaned[f] = int(raw) if raw.lstrip("-").isdigit() else 0
        return cleaned

    def _check_corner(self, data: dict) -> None:
        """
        Java cornerControl: in Russia, if promo contains 'Корнер', a Corner No
        is required. Raises PharmacyValidationError otherwise.
        """
        country = (data.get("country") or "").strip()
        promo = (data.get("promo") or "")
        corner_raw = str(data.get("cornerNo", "")).strip()
        corner_no = int(corner_raw) if corner_raw.lstrip("-").isdigit() else 0
        if country == "Russia" and "Корнер" in promo and corner_no == 0:
            raise PharmacyValidationError(
                "Для промо «Корнер» в России необходимо указать Corner No."
            )

    def create(self, brand: str, data: dict, user_name: str = ""):
        """Insert a new pharmacy row (status=1) into the brand's table."""
        from django.utils import timezone

        self._check_corner(data)
        model = self.repository._model_for(brand)
        fields = self._clean(data)
        fields["status"] = 1
        fields["entry_user"] = user_name
        fields["entry_date"] = timezone.now()
        # Bounty tablosunda brand kolonu var — doldur
        if model.__name__ == "PharmacyBounty":
            fields["brand"] = "BN"
        return model.objects.create(**fields)

    def update(self, brand: str, pharmacy_id: int, data: dict, user_name: str = "") -> int:
        """Update an existing pharmacy row in the brand's table."""
        from django.utils import timezone

        self._check_corner(data)
        model = self.repository._model_for(brand)
        fields = self._clean(data)
        fields["entry_user"] = user_name
        fields["entry_date"] = timezone.now()
        return model.objects.filter(pk=pharmacy_id).update(**fields)

    def soft_delete(self, brand: str, pharmacy_id: int) -> int:
        """Soft-delete: status=0 so the row drops out of the active list."""
        model = self.repository._model_for(brand)
        return model.objects.filter(pk=pharmacy_id).update(status=0)


# ============================ SERVICE ============================

class ReportService:
    """
    Orchestrates the Sales Report Observation screen (Phase 1: CHAIN_SALES,
    monthly). Wraps ReportRepository: provides filter dropdowns and runs the
    report.
    """

    COMP_TYPES = [("SL", "SOLGAR"), ("OS", "OBF"), ("BN", "NATURES BOUNTY")]

    def __init__(self):
        from .repositories import ReportRepository

        self.repository = ReportRepository()

    def dropdown_options(self, comp_type: str = "SL") -> dict:
        """Top-level filter dropdowns for the given brand (initial page load)."""
        groups = {}
        try:
            from .repositories import SalesRepository
            groups = SalesRepository().group_options()
        except Exception:
            groups = {}
        return {
            "chains": self.repository.filter_chains(comp_type),
            "countries": self.repository.filter_countries(comp_type),
            "main_groups": list(groups.get("main_groups", [])),
            "sub_groups": list(groups.get("sub_groups", [])),
        }

    def cascade_options(self, level: str, country: str = "", area: str = "",
                        region: str = "") -> list:
        """
        One cascading geographic list for the Country -> Area -> Region -> City
        cascade, narrowed by the parent selections.

        level: 'area' | 'region' | 'city'
        """
        if level == "area":
            return self.repository.filter_areas(country=country)
        if level == "region":
            return self.repository.filter_regions(country=country, area=area)
        if level == "city":
            return self.repository.filter_cities(country=country, area=area, region=region)
        return []

    def product_names(self, main_group: str = "", sub_group: str = "") -> list:
        """Product names for the selected main/sub group (cascading)."""
        try:
            from .repositories import SalesRepository
            names = SalesRepository().product_names_for_group(main_group, sub_group)
            return sorted(names) if names else []
        except Exception:
            return []

    def run_chain_sales(self, comp_type: str, begin: str, end: str,
                        chain: str = "", country: str = "", area: str = "",
                        region: str = "", city: str = "", medrep: str = "",
                        main_group: str = "", sub_group: str = "",
                        product_name: str = "") -> dict:
        """Run the CHAIN_SALES monthly report. Returns {columns, rows, total_rows}."""
        result = self.repository.chain_sales_monthly(
            comp_type=comp_type, begin=begin, end=end, chain=chain, country=country,
            area=area, region=region, city=city, medrep=medrep,
            main_group=main_group, sub_group=sub_group, product_name=product_name,
        )
        return {
            "columns": result["columns"],
            "rows": result["rows"],
            "total_rows": len(result["rows"]),
        }
