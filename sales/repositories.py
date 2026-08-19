"""
sales app — data access layer. ORM only, no raw SQL.
"""

from django.db.models import QuerySet

from .models import SalesRecord


class SalesRepository:
    """Encapsulates database access for sales records."""

    def bulk_create(self, records: list[SalesRecord]) -> int:
        """Insert many records at once. Returns the number created."""
        created = SalesRecord.objects.bulk_create(records)
        return len(created)

    def recent(self, limit: int = 100) -> QuerySet:
        """Return the most recent sales records."""
        return SalesRecord.objects.select_related("uploaded_by")[:limit]

    def for_report(self, report_date, chain_name: str) -> QuerySet:
        """Return records for a specific report date and chain."""
        return SalesRecord.objects.filter(
            report_date=report_date, chain_name=chain_name
        )

    def exists_for_report(self, report_date, chain_name: str) -> bool:
        """Check whether records already exist for this date and chain."""
        return SalesRecord.objects.filter(
            report_date=report_date, chain_name=chain_name
        ).exists()

    def filter_records(
        self, report_date=None, chain_name: str = "", country: str = "",
        brand: str = "", city: str = "", search: str = "",
    ) -> QuerySet:
        """
        Return sales records matching the given filters. Empty filters are
        ignored, so passing nothing returns everything.
        """
        qs = SalesRecord.objects.select_related("uploaded_by")

        if report_date:
            qs = qs.filter(report_date=report_date)
        if chain_name:
            qs = qs.filter(chain_name=chain_name)
        if country:
            qs = qs.filter(country=country)
        if brand:
            qs = qs.filter(brand=brand)
        if city:
            qs = qs.filter(city__icontains=city)
        if search:
            qs = qs.filter(product_name__icontains=search)

        return qs

    def filter_by_range(
        self, date_from=None, date_to=None, chain_name: str = "",
        country: str = "", brand: str = "", city: str = "", search: str = "",
    ) -> QuerySet:
        """
        Return sales records within a date range and matching filters.
        Empty filters are ignored.
        """
        qs = SalesRecord.objects.select_related("uploaded_by")

        if date_from:
            qs = qs.filter(report_date__gte=date_from)
        if date_to:
            qs = qs.filter(report_date__lte=date_to)
        if chain_name:
            qs = qs.filter(chain_name=chain_name)
        if country:
            qs = qs.filter(country=country)
        if brand:
            qs = qs.filter(brand=brand)
        if city:
            qs = qs.filter(city__icontains=city)
        if search:
            qs = qs.filter(product_name__icontains=search)

        return qs.order_by("chain_name", "product_name")

    def distinct_report_dates(self) -> list:
        """Return the distinct report dates present, newest first."""
        return list(
            SalesRecord.objects.values_list("report_date", flat=True)
            .distinct()
            .order_by("-report_date")
        )

    def distinct_chains(self, country: str = "") -> list[str]:
        """Return distinct chain names from ChainDefinition, optionally by country."""
        from .models import ChainDefinition

        qs = ChainDefinition.objects.filter(is_active=True)
        if country:
            qs = qs.filter(country=country)
        return list(
            qs.exclude(name="")
            .values_list("name", flat=True)
            .distinct().order_by("name")
        )

    def group_options(self, country: str = "") -> dict:
        """
        Distinct product groups and geographic regions for filter dropdowns.
        If country is given, regions/districts are limited to that country.
        """
        from .models import AddressGroup, ProductGroup

        main_groups = list(
            ProductGroup.objects.exclude(product_main_group="")
            .values_list("product_main_group", flat=True).distinct().order_by("product_main_group")
        )
        sub_groups = list(
            ProductGroup.objects.exclude(product_sub_group="")
            .values_list("product_sub_group", flat=True).distinct().order_by("product_sub_group")
        )

        addr_qs = AddressGroup.objects.all()
        if country:
            addr_qs = addr_qs.filter(cntry=country)   # AddressGroup'ta ülke bilgisi cntry kolonunda

        regions = list(
            addr_qs.exclude(region="")
            .values_list("region", flat=True).distinct().order_by("region")
        )
        districts = list(
            addr_qs.exclude(district="")
            .values_list("district", flat=True).distinct().order_by("district")
        )
        return {"main_groups": main_groups, "sub_groups": sub_groups,
                "regions": regions, "districts": districts}

    def product_names_for_group(self, main_group: str = "", sub_group: str = "") -> set:
        """Return lowercased product names in a group (for matching sales rows)."""
        from .models import ProductGroup

        qs = ProductGroup.objects.all()
        if main_group:
            qs = qs.filter(product_main_group=main_group)
        if sub_group:
            qs = qs.filter(product_sub_group=sub_group)
        return {name.lower() for name in qs.values_list("product_sales_name", flat=True) if name}

    def cities_for_region(self, region: str = "", district: str = "") -> set:
        """Return lowercased city names in a region/district (for matching sales rows)."""
        from .models import AddressGroup

        qs = AddressGroup.objects.all()
        if region:
            qs = qs.filter(region=region)
        if district:
            qs = qs.filter(district=district)
        return {c.lower() for c in qs.values_list("city_region", flat=True) if c}


class DistributorRepository:
    """Data access for distributor records."""

    def filter_records(
        self, distributor: str = "", operation_type: str = "",
        date_from=None, date_to=None, country: str = "",
        brand: str = "", city: str = "", search: str = "",
    ) -> QuerySet:
        """Return distributor records matching the filters. Empty ones ignored."""
        from .models import DistributorRecord

        qs = DistributorRecord.objects.all()
        if distributor:
            qs = qs.filter(distributor=distributor)
        if operation_type:
            qs = qs.filter(operation_type=operation_type)
        if date_from:
            qs = qs.filter(begin_date__gte=date_from)
        if date_to:
            qs = qs.filter(end_date__lte=date_to)
        if country:
            qs = qs.filter(country=country)
        if brand:
            qs = qs.filter(brand=brand)
        if city:
            qs = qs.filter(city__icontains=city)
        if search:
            qs = qs.filter(product_name__icontains=search)
        return qs.order_by("distributor", "product_name")

    def distinct_distributors(self) -> list[str]:
        """Distinct distributor names present in the data."""
        from .models import DistributorRecord

        return list(
            DistributorRecord.objects.exclude(distributor="")
            .values_list("distributor", flat=True)
            .distinct().order_by("distributor")
        )


class DoctorRepository:
    """
    Data access for Doctor records (external doctor_data table).

    Cascading address options come from the distinct values already present
    in doctor_data — country -> area -> region -> city — mirroring the Java
    getPRMDataGroupBy chain (which read prm_sales_addresses). Each level is
    filtered by the level(s) above it. Medrep / specialty / unified_specialty
    are likewise derived from existing doctor_data values.
    """

    def _distinct(self, field: str, **filters) -> list:
        """Distinct non-empty values of `field`, filtered, ordered."""
        from .models import Doctor

        qs = Doctor.objects.filter(status=1)
        for key, value in filters.items():
            if value:
                qs = qs.filter(**{key: value})
        return list(
            qs.exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values_list(field, flat=True)
            .distinct()
            .order_by(field)
        )

    # --- address cascade: country -> area -> region -> city ---

    def countries(self) -> list:
        """All distinct countries."""
        return self._distinct("country")

    def areas(self, country: str = "") -> list:
        """Distinct areas, optionally within a country."""
        return self._distinct("area", country=country)

    def regions(self, country: str = "", area: str = "") -> list:
        """Distinct regions, optionally within a country/area."""
        return self._distinct("region", country=country, area=area)

    def cities(self, country: str = "", area: str = "", region: str = "") -> list:
        """Distinct cities, optionally within country/area/region."""
        return self._distinct("city", country=country, area=area, region=region)

    def districts(self, country: str = "", area: str = "", region: str = "") -> list:
        """Distinct districts. Java's district combo is a flat list, but we
        allow the same cascading filters for consistency."""
        return self._distinct("district", country=country, area=area, region=region)

    # --- other dropdowns derived from doctor_data ---

    def medreps(self, brand: str = "", country: str = "", area: str = "") -> list:
        """Distinct medical reps, optionally narrowed by brand/country/area.

        Java getMedRep read from an employee list; here we derive medreps
        from the values already present in doctor_data."""
        return self._distinct("medrep", brand=brand, country=country, area=area)

    def specialties(self) -> list:
        """Distinct specialties present in doctor_data."""
        return self._distinct("specialty")

    def unified_specialties(self) -> list:
        """Distinct unified specialties present in doctor_data."""
        return self._distinct("unified_specialty")

class PharmacyRepository:
    """
    Data access for pharmacy records. Solgar/OBF and Bounty live in separate
    tables (pharmacy_data_solgar / pharmacy_data_bounty), so every query is
    routed to the right model by brand via _model_for.

    Dropdown options (address cascade, chain, category, etc.) are derived as
    DISTINCT values from the pharmacy table itself. When the app DB user is
    granted access to solgar_prm, these can be switched to the clean
    prm_sales_* reference tables with minimal change.
    """

    # Görünmez / sorunlu karakterler (Word'den yapışan) — metro vb. temizliği.
    _JUNK_CHARS = ("\xa0", "\u200e", "\u200f", "\ufeff")

    def _model_for(self, brand: str = ""):
        """Return the pharmacy model matching the brand (default: Solgar)."""
        from .models import PharmacyBounty, PharmacySolgar

        b = (brand or "").strip().upper()
        if b in ("BOUNTY", "NATURES BOUNTY", "NATURE'S BOUNTY", "BN"):
            return PharmacyBounty
        # SOLGAR, OBF ve bilinmeyen -> Solgar tablosu
        return PharmacySolgar

    def _clean(self, value: str) -> str:
        """Strip invisible junk characters and surrounding whitespace."""
        if value is None:
            return ""
        for ch in self._JUNK_CHARS:
            value = value.replace(ch, "")
        return value.strip()

    def _distinct(self, brand: str, field: str, **filters) -> list:
        """Distinct cleaned, non-empty values of `field` for a brand, filtered."""
        model = self._model_for(brand)
        qs = model.objects.all()
        for key, value in filters.items():
            if value:
                qs = qs.filter(**{key: value})
        raw = (
            qs.exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values_list(field, flat=True)
            .distinct()
        )
        # Temizle + tekrar tekilleştir (strip sonrası çakışabilir) + sırala
        cleaned = {self._clean(v) for v in raw if v and self._clean(v)}
        return sorted(cleaned)

    # --- address cascade: country -> area -> region -> city -> metro ---

    def countries(self, brand: str = "") -> list:
        """Distinct countries for a brand."""
        return self._distinct(brand, "country")

    def areas(self, brand: str = "", country: str = "") -> list:
        """Distinct areas within a country."""
        return self._distinct(brand, "area", country=country)

    def regions(self, brand: str = "", country: str = "", area: str = "") -> list:
        """Distinct regions within country/area."""
        return self._distinct(brand, "region", country=country, area=area)

    def cities(self, brand: str = "", country: str = "", area: str = "", region: str = "") -> list:
        """Distinct cities within country/area/region."""
        return self._distinct(brand, "city", country=country, area=area, region=region)

    def metros(self, brand: str = "", city: str = "") -> list:
        """Distinct metros for a city (values cleaned of invisible chars)."""
        return self._distinct(brand, "metro", city=city)

    def districts(self, brand: str = "", country: str = "", area: str = "", region: str = "") -> list:
        """Distinct districts within country/area/region."""
        return self._distinct(brand, "district", country=country, area=area, region=region)

    # --- other dropdowns derived from the pharmacy table ---

    def chains(self, brand: str = "") -> list:
        """Distinct group companies (chains)."""
        return self._distinct(brand, "group_company")

    def subchains(self, brand: str = "", group_company: str = "") -> list:
        """Distinct sub-chains, optionally within a chain."""
        return self._distinct(brand, "subgroup_company", group_company=group_company)

    def pharmacy_categories(self, brand: str = "") -> list:
        """Distinct pharmacy categories."""
        return self._distinct(brand, "pharmacy_category")

    def pharmacy_types(self, brand: str = "") -> list:
        """Distinct pharmacy types."""
        return self._distinct(brand, "pharmacy_type")

    def promos(self, brand: str = "") -> list:
        """Distinct promo values."""
        return self._distinct(brand, "promo")

    def assortiments(self, brand: str = "") -> list:
        """Distinct assortiment values."""
        return self._distinct(brand, "assortiment")

    def pharmacy_groups(self, brand: str = "") -> list:
        """Distinct pharmacy groups."""
        return self._distinct(brand, "pharmacy_group")

    def marketing_staff(self, brand: str = "", country: str = "", area: str = "") -> list:
        """Distinct marketing staff (medreps), optionally by country/area."""
        return self._distinct(brand, "marketing_staff", country=country, area=area)


class ReportRepository:
    """
    Builds and runs the Sales Report Observation query (Java repChainSalesNew).

    Phase 1 scope: CHAIN_SALES report type, MONTHLY date parameter, SALE
    operation. The brand-specific FROM/JOIN fragment is read from DadQuery
    (mirroring Java's getQueryScript); the SELECT header, monthly pivot
    columns, filters and grouping are built here.

    SECURITY: user-supplied values are passed as query parameters (%s), never
    string-concatenated, closing the SQL-injection hole present in the Java
    original. Month pivot column names are derived from the date range (not
    user input), so they are safe to inline.
    """

    # compType -> (brand label used in pivot subquery, product_type in WHERE)
    _BRAND_MAP = {
        "SL": ("SOLGAR", "SL"),
        "OS": ("OSB", "OS"),
        "BN": ("BOUNTY", "BN"),
    }
    _MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def __init__(self):
        from .models import DadQuery

        self._DadQuery = DadQuery

    def _script(self, name: str) -> str:
        """Fetch a named SQL fragment from the DadQuery store."""
        try:
            return self._DadQuery.objects.get(query_name=name, is_active=True).query_script
        except self._DadQuery.DoesNotExist:
            raise ValueError(f"SQL script not found: {name}")

    def _where_condition_name(self, comp_type: str, has_category: bool, has_product: bool,
                              rep_type: str) -> str:
        """Pick the FROM/JOIN script name, mirroring Java's selection logic."""
        ct = comp_type.upper()
        cat_rep = rep_type in ("CATEGORY_PRODUCT_SALES", "PRODUCT_SALES", "REGIONAL_PRODUCT_SALES")
        use_cat = has_category or has_product or cat_rep
        suffix = "_CAT" if use_cat else ""
        return f"CHAIN_SALES_WHRE_CONDITION_{ct}{suffix}"

    def _month_iter(self, begin_yyyymmdd: str, end_yyyymmdd: str):
        """
        Yield (year, month_abbr, month_num) for each month in the range.
        Dates are 'YYYYMMDD' strings (as the Java UI passes them).
        """
        from datetime import date

        by, bm = int(begin_yyyymmdd[:4]), int(begin_yyyymmdd[4:6])
        ey, em = int(end_yyyymmdd[:4]), int(end_yyyymmdd[4:6])
        y, m = by, bm
        while (y < ey) or (y == ey and m <= em):
            yield y, self._MONTHS[m - 1], f"{m:02d}"
            m += 1
            if m > 12:
                m = 1
                y += 1

    def _monthly_pivot(self, begin: str, end: str, comp_type: str) -> str:
        """
        Build the monthly SUM pivot columns + pharmacy_count + Total, matching
        Java chainSalesFromMonthly. Column names are date-derived (safe to inline).
        """
        cols = []
        for year, mon_abbr, mon_num in self._month_iter(begin, end):
            # sum(case when year matches and month matches then sales_count else 0)
            col = (
                f"sum(case when substring(sales_date,1,4)='{year}' "
                f"THEN (case when substring(sales_date,6,2)='{mon_num}' "
                f"then sales_count else 0 end) else 0 END) as `{year}_{mon_abbr}`"
            )
            cols.append(col)

        brand_label, _ = self._BRAND_MAP.get(comp_type.upper(), ("SOLGAR", "SL"))
        if brand_label == "SOLGAR":
            pcount = ("(select count(*) from solgar_tst.pharmacy_data_solgar k "
                      "where status = 1 and a.main_group = k.group_company "
                      "and pharmacy_Activeness ='Актив') as pharmacy_count")
        elif brand_label == "OSB":
            pcount = ("(select count(*) from solgar_tst.pharmacy_data_bounty k "
                      "where status = 1 and a.main_group = k.group_company "
                      "and pharmacy_Activeness ='Актив' and brand = 'OS') as pharmacy_count")
        else:  # BOUNTY
            pcount = ("(select count(*) from solgar_tst.pharmacy_data_bounty k "
                      "where status = 1 and a.main_group = k.group_company "
                      "and pharmacy_Activeness ='Актив' and brand = 'BN') as pharmacy_count")

        return ", ".join(cols) + ", " + pcount + ", sum(sales_count) as Total "

    def chain_sales_monthly(self, comp_type: str, begin: str, end: str,
                            chain: str = "", country: str = "", area: str = "",
                            region: str = "", city: str = "", medrep: str = "") -> dict:
        """
        CHAIN_SALES report, monthly, SALE. Returns {columns, rows}.

        begin/end: 'YYYYMMDD'. comp_type: SL/OS/BN. Filters optional.
        """
        from django.db import connections

        comp_type = (comp_type or "SL").upper()
        _, product_type = self._BRAND_MAP.get(comp_type, ("SOLGAR", "SL"))
        brand_label = self._BRAND_MAP.get(comp_type, ("SOLGAR",))[0]

        # 1) SELECT header: marka etiketi + chain + aylık pivot
        select_head = f"select '{brand_label}' as PRODUCT, a.main_group as chain, "
        pivot = self._monthly_pivot(begin, end, comp_type)

        # 2) FROM/JOIN + base where (script'ten). Script zaten 'where product_type=..' içeriyor.
        where_script = self._script(self._where_condition_name(comp_type, bool(0), bool(0), "CHAIN_SALES"))

        # 3) tarih + filtreler — PARAMETRELİ
        params = []
        # Tarih karsilastirmasi: sales_date datetime oldugu icin dogrudan
        # date siniri kullaniyoruz. Java string hilesi (replace(sales_date,'-',''))
        # bitis gununun saatli kayitlarini eliyordu; asagidaki hem dogru hem indeks dostu.
        # begin/end 'YYYYMMDD' -> 'YYYY-MM-DD'. Bitis gununun tamamini kapsamak icin
        # ertesi gunun basindan kucuk kosulu kullaniyoruz.
        from datetime import datetime, timedelta
        begin_dt = datetime.strptime(begin, "%Y%m%d").strftime("%Y-%m-%d")
        end_next = (datetime.strptime(end, "%Y%m%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        where_extra = " and sales_date >= %s and sales_date < %s "
        params.extend([begin_dt, end_next])

        if chain:
            where_extra += " and a.main_group = %s "
            params.append(chain)
        if country:
            where_extra += " and a.country = %s "
            params.append(country)
        if area:
            where_extra += " and e.country = %s "
            params.append(area)
        if region:
            where_extra += " and e.region = %s "
            params.append(region)
        if city:
            where_extra += " and e.city = %s "
            params.append(city)
        if medrep:
            where_extra += " and marketing_staff = %s "
            params.append(medrep)

        group_by = " group by a.main_group order by Total desc "

        sql = select_head + pivot + where_script + where_extra + group_by

        with connections["refdb"].cursor() as cur:
            cur.execute(sql, params)
            columns = [c[0] for c in cur.description]
            rows = cur.fetchall()

        return {"columns": columns, "rows": rows, "sql": sql}

    # --- filter dropdown options (Phase 1: distinct from sales_pharmacy) ---

    def filter_chains(self, comp_type: str = "SL") -> list:
        """Distinct chains (main_group) for a brand, from sales data."""
        from django.db import connections

        _, product_type = self._BRAND_MAP.get((comp_type or "SL").upper(), ("SOLGAR", "SL"))
        sql = ("SELECT DISTINCT main_group FROM solgar_tst.sales_pharmacy "
               "WHERE product_type = %s AND main_group IS NOT NULL AND main_group <> '' "
               "ORDER BY main_group")
        with connections["refdb"].cursor() as cur:
            cur.execute(sql, [product_type])
            return [r[0] for r in cur.fetchall()]

    def filter_countries(self, comp_type: str = "SL") -> list:
        """Distinct countries for a brand, from sales data."""
        from django.db import connections

        _, product_type = self._BRAND_MAP.get((comp_type or "SL").upper(), ("SOLGAR", "SL"))
        sql = ("SELECT DISTINCT country FROM solgar_tst.sales_pharmacy "
               "WHERE product_type = %s AND country IS NOT NULL AND country <> '' "
               "ORDER BY country")
        with connections["refdb"].cursor() as cur:
            cur.execute(sql, [product_type])
            return [r[0] for r in cur.fetchall()]
