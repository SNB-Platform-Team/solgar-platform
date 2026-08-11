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
BOUNTY_KEYWORDS = (
    "natures bounty",
    "nature s bounty",
    "нэйчес",
    "нэйчерс",
    "баунти",
    "нб ",
    " нб",
    "nb ",
    "nature bounty",
    "n b",
)


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
        """Read the first worksheet into a list of rows (.xls or .xlsx)."""
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

    def filter_options(self) -> dict:
        """Return distinct values for the filter dropdowns."""
        return {
            "report_dates": self.repository.distinct_report_dates(),
            "chains": self.repository.distinct_chains(),
        }

    def chain_report(self, **filters) -> dict:
        """
        Run a date-range chain-sales query and compute brand totals.

        Returns a dict with records and aggregated Solgar/Bounty totals.
        """
        from django.db.models import Sum

        records = self.repository.filter_by_range(**filters)

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

        self.repository = DistributorRepository()

    def query(self, **filters) -> dict:
        """Filtered query with Solgar/Bounty totals."""
        from django.db.models import Sum
        from .models import DistributorRecord

        records = self.repository.filter_records(**filters)
        solgar = records.filter(brand=DistributorRecord.Brand.SOLGAR).aggregate(
            c=Sum("count"), a=Sum("amount")
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

class DistributorViewService:
    """View and aggregate saved distributor records."""

    def __init__(self) -> None:
        """Wire up the repository."""
        from .repositories import DistributorRepository

        self.repository = DistributorRepository()

    def query(self, **filters) -> dict:
        """Filtered query with Solgar/Bounty totals."""
        from django.db.models import Sum
        from .models import DistributorRecord

        records = self.repository.filter_records(**filters)
        solgar = records.filter(brand=DistributorRecord.Brand.SOLGAR).aggregate(
            c=Sum("count"), a=Sum("amount")
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



































        