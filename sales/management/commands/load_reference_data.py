"""
Load reference data (product groups, address groups) from CSV exports.

Usage:
    python manage.py load_reference_data --products path/to/sales_product_group.csv
    python manage.py load_reference_data --addresses path/to/solgar_address_group.csv
"""

import csv

from django.core.management.base import BaseCommand

from sales.models import AddressGroup, ProductGroup


class Command(BaseCommand):
    """Load product and address reference data from CSV files."""

    help = "Load product/address reference data from CSV exports."

    def add_arguments(self, parser):
        """Define CLI arguments."""
        parser.add_argument("--products", type=str, help="Path to sales_product_group CSV")
        parser.add_argument("--addresses", type=str, help="Path to solgar_address_group CSV")

    def handle(self, *args, **options):
        """Run the import."""
        if options["products"]:
            self._load_products(options["products"])
        if options["addresses"]:
            self._load_addresses(options["addresses"])
        if not options["products"] and not options["addresses"]:
            self.stdout.write(self.style.WARNING("Nothing to load. Use --products or --addresses."))

    def _load_products(self, path):
        """Load product groups (semicolon-delimited CSV)."""
        ProductGroup.objects.all().delete()
        created = 0
        batch = []
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                name = (row.get("product_sales_name") or "").strip()
                if not name:
                    continue
                batch.append(ProductGroup(
                    product_sales_name=name,
                    match_key=name.lower(),
                    main_group=(row.get("product_main_group") or "").strip(),
                    sub_group=(row.get("product_sub_group") or "").strip(),
                ))
                if len(batch) >= 2000:
                    ProductGroup.objects.bulk_create(batch)
                    created += len(batch)
                    batch = []
        if batch:
            ProductGroup.objects.bulk_create(batch)
            created += len(batch)
        self.stdout.write(self.style.SUCCESS(f"Loaded {created} product groups."))

    def _load_addresses(self, path):
        """Load address groups (comma-delimited CSV)."""
        AddressGroup.objects.all().delete()
        created = 0
        batch = []
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                # The Cyrillic city name in 'city_region' is what matches sales rows.
                city = (row.get("city_region") or "").strip()
                if not city:
                    continue
                batch.append(AddressGroup(
                    city_name=city,
                    match_key=city.lower(),
                    region=(row.get("region") or "").strip(),
                    district=(row.get("district") or "").strip(),
                    country=(row.get("cntry") or "").strip(),
                ))
                if len(batch) >= 2000:
                    AddressGroup.objects.bulk_create(batch)
                    created += len(batch)
                    batch = []
        if batch:
            AddressGroup.objects.bulk_create(batch)
            created += len(batch)
        self.stdout.write(self.style.SUCCESS(f"Loaded {created} address groups."))