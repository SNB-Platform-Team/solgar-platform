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


class MFOSalesParser:
    """
    Parser for the MFO chain vertical Excel format.

    Column headers expected (Russian), matched case-insensitively:
      - product:          Номенклатура
      - pharmacy/address:  Адрес грузополучателя
      - city:              Город
      - count (sales):     Продажи
      - amount:            Сумма в руб.
      - remaining count:   Остаток на конец периода
    """

    COLUMNS = {
        "product": "номенклатура",
        "pharmacy": "адрес грузополучателя",
        "city": "город",
        "count": "продажи",
        "amount": "сумма в руб.",
        "remaining_count": "остаток на конец периода",
    }

    def _read_sheet(self, file_obj, filename: str = "") -> list[list]:
        """
        Read the first worksheet into a list of rows (each a list of cell
        values), supporting both .xlsx (openpyxl) and .xls (xlrd).

        Args:
            file_obj: The uploaded file object.
            filename: The original filename, used to detect the format.

        Returns:
            A list of rows; each row is a list of cell values.

        Raises:
            SalesParseError: If the file cannot be opened.
        """
        name = (filename or getattr(file_obj, "name", "")).lower()

        if name.endswith(".xls"):
            # Old binary .xls format — use xlrd.
            try:
                import xlrd

                file_obj.seek(0)
                data = file_obj.read()
                book = xlrd.open_workbook(file_contents=data)
                sheet = book.sheet_by_index(0)
                rows = []
                for r in range(sheet.nrows):
                    rows.append([sheet.cell_value(r, c) for c in range(sheet.ncols)])
                return rows
            except ImportError as exc:
                raise SalesParseError(
                    "Для чтения .xls требуется библиотека xlrd."
                ) from exc
            except Exception as exc:
                raise SalesParseError(f"Не удалось открыть .xls файл: {exc}") from exc
        else:
            # .xlsx / .xlsm — use openpyxl.
            try:
                file_obj.seek(0)
                wb = load_workbook(file_obj, data_only=True, read_only=True)
            except Exception as exc:
                raise SalesParseError(f"Не удалось открыть файл: {exc}") from exc
            ws = wb.active
            rows = []
            for row in ws.iter_rows(values_only=True):
                rows.append(list(row))
            return rows

    def classify(self, product_name: str) -> str:
        """
        Classify a product by its name.

        Rule: if the name contains a Nature's Bounty marker, it is Bounty;
        otherwise it is Solgar. These files contain only Solgar and Bounty
        products, so anything not recognisably Bounty is treated as Solgar,
        including names with no brand text.
        """
        # Normalise: lowercase and unify apostrophe variants so "Nature's",
        # "Nature’s" and "Natures" all match the same marker.
        name = product_name.lower()
        for apo in ("’", "‘", "`", "'"):
            name = name.replace(apo, "")

        if any(kw in name for kw in BOUNTY_KEYWORDS):
            return SalesRecord.Brand.BOUNTY
        return SalesRecord.Brand.SOLGAR

    def _to_int(self, value: Any) -> int:
        """Best-effort convert a cell value to int; 0 on failure."""
        if value is None or value == "":
            return 0
        try:
            # handle "12", "12.0", "12,0"
            s = str(value).replace(",", ".").strip()
            return int(float(s))
        except (ValueError, TypeError):
            return 0

    def _to_decimal(self, value: Any) -> Decimal:
        """Best-effort convert a cell value to Decimal; 0 on failure."""
        if value is None or value == "":
            return Decimal("0")
        try:
            s = str(value).replace(",", ".").strip()
            return Decimal(s).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    def _find_header(self, rows: list[list]) -> tuple[int, dict[str, int]]:
        """
        Locate the header row and map logical fields to column indexes.

        Args:
            rows: The sheet as a list of rows.

        Returns:
            (header_row_index, {field: column_index})

        Raises:
            SalesParseError: If the product column is not found.
        """
        wanted = self.COLUMNS
        for row_idx in range(min(len(rows), 30)):
            found: dict[str, int] = {}
            for col_idx, value in enumerate(rows[row_idx]):
                if value is None:
                    continue
                cell_text = str(value).strip().lower()
                for fieldname, header in wanted.items():
                    if cell_text == header:
                        found[fieldname] = col_idx
            if "product" in found:
                return row_idx, found
        raise SalesParseError(
            "Не удалось найти заголовок «Номенклатура» в файле."
        )

    def parse(self, file_obj, filename: str = "") -> ParseResult:
        """
        Parse an uploaded Excel file (.xls or .xlsx) into a ParseResult.

        Args:
            file_obj: A file-like object (the uploaded file).
            filename: Original filename, used to pick the reader.

        Returns:
            ParseResult with rows and computed totals.

        Raises:
            SalesParseError: If the file cannot be read or has no header.
        """
        rows = self._read_sheet(file_obj, filename)
        if not rows:
            return ParseResult()

        header_row, cols = self._find_header(rows)

        result = ParseResult()
        seen_products: set[str] = set()

        for row_idx in range(header_row + 1, len(rows)):
            row = rows[row_idx]

            def cell(fieldname: str):
                col = cols.get(fieldname)
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
        self.parser = MFOSalesParser()

    def preview(self, file_obj, filename: str = "") -> ParseResult:
        """Parse a file and return the result for preview (no saving)."""
        return self.parser.parse(file_obj, filename)

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