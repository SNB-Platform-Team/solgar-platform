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

    def distinct_chains(self) -> list[str]:
        """Return the distinct chain names present."""
        return list(
            SalesRecord.objects.exclude(chain_name="")
            .values_list("chain_name", flat=True)
            .distinct()
            .order_by("chain_name")
        )


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