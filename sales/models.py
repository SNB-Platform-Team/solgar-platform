"""
sales app - pharmacy chain sales data.

Sales records are uploaded from chain Excel files, one row per product line.
Each record is classified as Solgar or Bounty based on the product name.
"""

from django.conf import settings
from django.db import models


class DistributorRecord(models.Model):
    """
    Distributor sales/stock line, uploaded from a distributor Excel file.

    Distinct from SalesRecord (pharmacy data): distributors carry extra
    fields (INN, segment, client, addresses) and an operation type
    (sale vs stock). Stored under the solgar_stk schema (table prefix).
    """

    class Brand(models.TextChoices):
        """Brand classification (mirrors SalesRecord.Brand)."""

        SOLGAR = "SOLGAR", "Solgar"
        BOUNTY = "BOUNTY", "Nature's Bounty"
        OTHER = "OTHER", "Other"

    class Operation(models.TextChoices):
        """Whether this row is a sale or a stock (inventory) record."""

        SALE = "SALE", "Продажа"
        STOCK = "STOCK", "Сток"

    distributor = models.CharField("Distributor", max_length=120)
    operation_type = models.CharField(
        "Operation type", max_length=10,
        choices=Operation.choices, default=Operation.SALE,
    )
    country = models.CharField("Country", max_length=60)
    begin_date = models.DateField("Begin date", null=True, blank=True)
    end_date = models.DateField("End date", null=True, blank=True)

    product_name = models.CharField("Product name", max_length=300)
    product_type = models.CharField("Product type", max_length=120, blank=True)
    brand = models.CharField(
        "Brand", max_length=10, choices=Brand.choices, default=Brand.OTHER
    )
    count = models.IntegerField("Count", default=0)
    amount = models.DecimalField("Amount", max_digits=14, decimal_places=2, default=0)

    city = models.CharField("City", max_length=150, blank=True)
    client = models.CharField("Client", max_length=300, blank=True)
    legal_address = models.CharField("Legal address", max_length=400, blank=True)
    actual_address = models.CharField("Actual address", max_length=400, blank=True)
    inn = models.CharField("INN", max_length=30, blank=True)
    segment = models.CharField("Segment", max_length=120, blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="distributor_uploads",
        verbose_name="Uploaded by",
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Distributor record"
        verbose_name_plural = "Distributor records"
        db_table = "solgar_stk_distributor_record"
        ordering = ["-begin_date", "distributor", "product_name"]
        indexes = [
            models.Index(fields=["distributor", "operation_type"]),
            models.Index(fields=["begin_date", "end_date"]),
            models.Index(fields=["brand"]),
        ]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.distributor} - {self.product_name} ({self.get_operation_type_display()})"


class BrandDefinition(models.Model):
    """
    Parametric brand definition. Instead of hard-coding brand keywords in
    the parser, each brand's markers live here. Deactivating a brand
    ('pulling it out') is a data change, not a code change.
    """

    name = models.CharField("Brand name", max_length=80, unique=True)
    code = models.CharField("Brand code", max_length=20, unique=True)
    keywords = models.JSONField("Keywords", default=list)
    is_default = models.BooleanField("Default brand", default=False)
    priority = models.IntegerField("Priority", default=100)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Brand definition"
        verbose_name_plural = "Brand definitions"
        db_table = "intern_sls_brand_definition"
        ordering = ["priority", "name"]

    def __str__(self) -> str:
        """Readable representation."""
        flags = []
        if self.is_default:
            flags.append("default")
        if not self.is_active:
            flags.append("inactive")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.name}{suffix}"


class ChainDefinition(models.Model):
    """
    Parametric definition of how to parse one chain/distributor's Excel.

    Instead of a separate parser per chain, a single parser reads these
    definitions. Adding a new chain means adding a row here, not new code.
    """

    class Orientation(models.TextChoices):
        """Excel layout: rows stacked vertically or spread horizontally."""

        VERTICAL = "VERTICAL", "Вертикальный"
        HORIZONTAL = "HORIZONTAL", "Горизонтальный"

    class SourceType(models.TextChoices):
        """Whether this definition describes a pharmacy chain or a distributor."""

        PHARMACY = "PHARMACY", "Аптечная сеть"
        DISTRIBUTOR = "DISTRIBUTOR", "Дистрибьютор"

    name = models.CharField("Chain / distributor name", max_length=120, unique=True)
    country = models.CharField("Country", max_length=60, default="Russia")
    source_type = models.CharField(
        "Source type", max_length=12,
        choices=SourceType.choices, default=SourceType.PHARMACY,
    )
    orientation = models.CharField(
        "Layout orientation", max_length=12,
        choices=Orientation.choices, default=Orientation.VERTICAL,
    )
    column_map = models.JSONField("Column mapping", default=dict)
    header_search_limit = models.IntegerField("Header search limit", default=30)
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Chain definition"
        verbose_name_plural = "Chain definitions"
        db_table = "intern_sls_chain_definition"
        ordering = ["name"]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.name} ({self.country}, {self.get_orientation_display()})"


class SalesRecord(models.Model):
    """A single product sales line from a chain's Excel report."""

    class Brand(models.TextChoices):
        """Which brand the product belongs to."""

        SOLGAR = "SOLGAR", "Solgar"
        BOUNTY = "BOUNTY", "Nature's Bounty"
        OTHER = "OTHER", "Other"

    report_date = models.DateField("Report date")
    chain_name = models.CharField("Chain name", max_length=120)
    country = models.CharField("Country", max_length=60)

    product_name = models.CharField("Product name", max_length=300)
    brand = models.CharField(
        "Brand", max_length=10, choices=Brand.choices, default=Brand.OTHER
    )
    pharmacy = models.CharField("Pharmacy / address", max_length=400, blank=True)
    city = models.CharField("City", max_length=150, blank=True)
    count = models.IntegerField("Sales count", default=0)
    amount = models.DecimalField("Sales amount", max_digits=14, decimal_places=2, default=0)
    remaining_count = models.IntegerField("Remaining stock count", default=0)
    remaining_amount = models.DecimalField(
        "Remaining stock amount", max_digits=14, decimal_places=2, default=0
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sales_uploads",
        verbose_name="Uploaded by",
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Sales record"
        verbose_name_plural = "Sales records"
        db_table = "sales_record"
        ordering = ["-report_date", "chain_name", "product_name"]
        indexes = [
            models.Index(fields=["report_date", "chain_name"]),
            models.Index(fields=["brand"]),
        ]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.product_name} - {self.count} ({self.get_brand_display()})"


class ProductGroup(models.Model):
    """
    Read-only mirror of solgar_tst.sales_product_group (external DB).
    Django does not manage this table; it only reads for report filters.
    """

    id = models.IntegerField(primary_key=True)
    product_type = models.CharField(max_length=5, blank=True)
    product_sales_name = models.CharField(max_length=255, blank=True)
    product_official_name = models.CharField(max_length=255, blank=True)
    product_official_id = models.IntegerField(null=True, blank=True)
    product_main_group = models.CharField(max_length=45, blank=True)
    product_sub_group = models.CharField(max_length=45, blank=True)

    class Meta:
        managed = False
        db_table = "sales_product_group"
        verbose_name = "Product group"
        verbose_name_plural = "Product groups"

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.product_sales_name} → {self.product_main_group}/{self.product_sub_group}"

    @property
    def match_key(self) -> str:
        """Lowercased product name for matching against sales rows."""
        return (self.product_sales_name or "").lower()


class AddressGroup(models.Model):
    """
    Read-only mirror of solgar_tst.solgar_address_group (external DB).
    Django does not manage this table; it only reads for report filters.
    """

    id = models.IntegerField(primary_key=True)
    cntry = models.CharField(max_length=45, blank=True)
    country = models.CharField(max_length=45, blank=True)
    region = models.CharField(max_length=45, blank=True)
    district = models.CharField(max_length=45, blank=True)
    city = models.CharField(max_length=45, blank=True)
    city_region = models.CharField(max_length=45, blank=True)
    administrative_area_name = models.CharField(max_length=45, blank=True)
    sub_administrative_area_name = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = "solgar_address_group"
        verbose_name = "Address group"
        verbose_name_plural = "Address groups"

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.city_region} → {self.region} / {self.district}"

    @property
    def match_key(self) -> str:
        """Lowercased city (Cyrillic) for matching against sales rows."""
        return (self.city_region or "").lower()


class Doctor(models.Model):
    """
    Read/write mirror of the external `doctor_data` table (refdb, Olga's
    MySQL). Backs the 'Врач вход Обновление' (Doctor Entry & Update) screen.

    managed=False: Django never creates or migrates this table; it only reads
    and writes rows. Column names match the live DB exactly (note the
    capitalised Specialty / Unified_specialty / Position_regalia columns).
    """

    id = models.AutoField(primary_key=True)
    status = models.IntegerField("Status", default=1)

    brand = models.CharField("Brand", max_length=45, blank=True, null=True)
    country = models.CharField("Country", max_length=12, blank=True, null=True)
    area = models.CharField("Area", max_length=45, blank=True, null=True)
    region = models.CharField("Region", max_length=25, blank=True, null=True)
    district = models.CharField("District", max_length=45, blank=True, null=True)
    city = models.CharField("City", max_length=45, blank=True, null=True)

    activeness = models.CharField("Activeness", max_length=12, blank=True, null=True)
    medrep = models.CharField("Marketing staff", max_length=255, blank=True, null=True)
    doctor_date = models.CharField("Activation date", max_length=12, blank=True, null=True)
    doctor_name = models.CharField("Doctor name", max_length=255, blank=True, null=True)
    unified_specialty = models.CharField(
        "Unified specialty", max_length=45, blank=True, null=True,
        db_column="Unified_specialty",
    )
    specialty = models.CharField(
        "Specialty", max_length=45, blank=True, null=True,
        db_column="Specialty",
    )
    position_regalia = models.CharField(
        "Position / regalia", max_length=255, blank=True, null=True,
        db_column="Position_regalia",
    )
    category = models.CharField("Category", max_length=5, blank=True, null=True)

    clinic_name = models.CharField("Clinic name", max_length=255, blank=True, null=True)
    clinic_name1 = models.CharField("Clinic name (text)", max_length=255, blank=True, null=True)
    clinic_status = models.CharField("Clinic status", max_length=45, blank=True, null=True)
    clinic_address = models.CharField("Clinic address", max_length=255, blank=True, null=True)
    clinic_count = models.IntegerField("Clinic count", blank=True, null=True)
    key_person = models.CharField("Key person", max_length=255, blank=True, null=True)

    doctor_tel = models.CharField("Doctor tel", max_length=100, blank=True, null=True)
    doctor_email = models.CharField("Doctor email", max_length=45, blank=True, null=True)

    full_address = models.CharField("Full address", max_length=255, blank=True, null=True)
    requested = models.CharField("Requested address", max_length=255, blank=True, null=True)
    building_type = models.CharField("Building type", max_length=255, blank=True, null=True)
    country_code = models.CharField("Country code", max_length=255, blank=True, null=True)
    administrative_area_name = models.CharField(
        "Administrative area name", max_length=255, blank=True, null=True
    )
    sub_administrative_area_name = models.CharField(
        "Sub administrative area name", max_length=255, blank=True, null=True
    )
    street = models.CharField("Street", max_length=255, blank=True, null=True)
    homenumber = models.CharField("Home number", max_length=255, blank=True, null=True)
    point_y = models.CharField("Point Y", max_length=255, blank=True, null=True)
    point_x = models.CharField("Point X", max_length=255, blank=True, null=True)

    doctor_id = models.IntegerField("Doctor id", default=0, blank=True, null=True)
    entry_date = models.DateTimeField("Entry date", blank=True, null=True)
    entry_user = models.CharField("Entry user", max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "doctor_data"
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.doctor_name or '-'} ({self.city or '-'}, {self.brand or '-'})"


class PharmacyBase(models.Model):
    """
    Abstract base for pharmacy records. The Solgar and Bounty brands live in
    separate physical tables (pharmacy_data_solgar / pharmacy_data_bounty)
    with identical columns, so the fields are defined once here and each
    concrete subclass only sets its db_table.

    managed=False on the concrete models: Django never creates/migrates these
    tables; it reads and writes rows. Backs the Java PharmacyEntryUpdate form.
    """

    id = models.AutoField(primary_key=True)

    country = models.CharField("Country", max_length=45, blank=True, null=True)
    area = models.CharField("Area", max_length=45, blank=True, null=True)
    region = models.CharField("Region", max_length=255, blank=True, null=True)
    city = models.CharField("City", max_length=255, blank=True, null=True)
    city_region = models.CharField("City region", max_length=255, blank=True, null=True)
    district = models.CharField("District", max_length=255, blank=True, null=True)
    metro = models.CharField("Metro", max_length=255, blank=True, null=True)

    group_company = models.CharField("Group company", max_length=255, blank=True, null=True)
    subgroup_company = models.CharField("Subgroup company", max_length=255, blank=True, null=True)
    pharmacy_no = models.CharField("Pharmacy no", max_length=255, blank=True, null=True)
    pharmacy_address = models.CharField("Pharmacy address", max_length=255, blank=True, null=True)
    pharmacy_category = models.CharField("Pharmacy category", max_length=5, blank=True, null=True)
    assortiment = models.CharField("Assortiment", max_length=45, blank=True, null=True)
    pharmacy_type = models.CharField("Pharmacy type", max_length=255, blank=True, null=True)
    promo = models.CharField("Promo", max_length=45, blank=True, null=True)
    marketing_staff = models.CharField("Marketing staff", max_length=255, blank=True, null=True)
    pharmacy_response_person = models.CharField("Pharmacy head name", max_length=255, blank=True, null=True)
    pharmacy_tel = models.CharField("Pharmacy tel", max_length=255, blank=True, null=True)
    pharmacy_email = models.CharField("Pharmacy email", max_length=255, blank=True, null=True)
    pharmacy_activeness = models.CharField("Pharmacy activeness", max_length=45, blank=True, null=True)
    pharmacy_activation_date = models.CharField("Activation date", max_length=255, blank=True, null=True)
    comments = models.CharField("Comments", max_length=255, blank=True, null=True, db_column="Comments")

    marketing_staff_no = models.IntegerField("Marketing staff no", blank=True, null=True)
    pharmacy_number_sale = models.CharField("Pharmacy number sale", max_length=255, blank=True, null=True)
    found_no = models.IntegerField("Found no", blank=True, null=True)

    full_address = models.CharField("Full address", max_length=255, blank=True, null=True)
    requested = models.CharField("Requested", max_length=255, blank=True, null=True)
    building_type = models.CharField("Building type", max_length=45, blank=True, null=True)
    country_code = models.CharField("Country code", max_length=45, blank=True, null=True)
    administrative_area_name = models.CharField("Administrative area name", max_length=255, blank=True, null=True)
    sub_administrative_area_name = models.CharField("Sub administrative area name", max_length=255, blank=True, null=True)
    street = models.CharField("Street", max_length=255, blank=True, null=True)
    homenumber = models.CharField("Home number", max_length=255, blank=True, null=True)
    point_y = models.CharField("Point Y", max_length=45, blank=True, null=True)
    point_x = models.CharField("Point X", max_length=45, blank=True, null=True)

    processed = models.IntegerField("Processed", blank=True, null=True)
    status = models.IntegerField("Status", blank=True, null=True)
    pharmacy_id = models.IntegerField("Pharmacy id", default=0, blank=True, null=True)
    assortiment1 = models.CharField("Assortiment 1 (OBF)", max_length=45, blank=True, null=True)
    pharmacy_group = models.CharField("Pharmacy group", max_length=45, blank=True, null=True)
    sku = models.IntegerField("SKU", default=0, blank=True, null=True)
    cornerNo = models.IntegerField("Corner no", default=0, blank=True, null=True, db_column="cornerNo")
    entry_user = models.CharField("Entry user", max_length=255, blank=True, null=True)
    entry_date = models.DateTimeField("Entry date", blank=True, null=True)

    pharmacist_name_1 = models.CharField("Pharmacist name 1", max_length=255, blank=True, null=True)
    pharmacy_home_tel = models.CharField("Pharmacist 1 tel", max_length=255, blank=True, null=True)
    pharmacist_name_2 = models.CharField("Pharmacist name 2", max_length=255, blank=True, null=True)
    pharmacy_work_tel = models.CharField("Pharmacist 2 tel", max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.group_company or '-'} - {self.city or '-'} ({self.country or '-'})"


class PharmacySolgar(PharmacyBase):
    """Solgar-brand pharmacies (pharmacy_data_solgar). Also used for OBF."""

    class Meta:
        managed = False
        db_table = "pharmacy_data_solgar"
        verbose_name = "Pharmacy (Solgar)"
        verbose_name_plural = "Pharmacies (Solgar)"


class PharmacyBounty(PharmacyBase):
    """
    Nature's Bounty pharmacies (pharmacy_data_bounty).

    This table has an extra `brand` column (default 'BN') absent from the
    Solgar table, so it is declared only here.
    """

    brand = models.CharField("Brand", max_length=45, blank=True, null=True, default="BN")

    class Meta:
        managed = False
        db_table = "pharmacy_data_bounty"
        verbose_name = "Pharmacy (Bounty)"
        verbose_name_plural = "Pharmacies (Bounty)"

class PrmAddress(models.Model):
    """
    Read-only mirror of solgar_prm.prm_sales_addresses.
    Source for the Country -> Area -> Region -> City address cascade
    (the Java getPRMDataGroupBy chain).
    """

    id = models.IntegerField(primary_key=True)
    country = models.CharField(max_length=45, blank=True)
    area = models.CharField(max_length=45, blank=True)
    district = models.CharField(max_length=45, blank=True)
    region = models.CharField(max_length=45, blank=True)
    city = models.CharField(max_length=45, blank=True)
    county = models.CharField(max_length=45, blank=True)

    class Meta:
        managed = False
        db_table = "`solgar_prm`.`prm_sales_addresses`"
        verbose_name = "PRM address"
        verbose_name_plural = "PRM addresses"

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.country} / {self.area} / {self.region} / {self.city}"


class PrmMetro(models.Model):
    """
    Read-only mirror of solgar_prm.prm_sales_metro.
    Source for the City -> Metro step (clean metro names).
    """

    id = models.IntegerField(primary_key=True)
    status = models.IntegerField(blank=True, null=True)
    city = models.CharField(max_length=45, blank=True)
    metro = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = "`solgar_prm`.`prm_sales_metro`"
        verbose_name = "PRM metro"
        verbose_name_plural = "PRM metros"

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.city} - {self.metro}"

class DadQuery(models.Model):
    """
    SQL script fragment store, mirroring Java's solgar_gen.dad_queries table.

    The Sales Report Observation screen builds its report by combining named
    SQL fragments (FROM/JOIN conditions per brand) with dynamically generated
    SELECT/pivot/filter clauses. Storing the fragments as data (not code) keeps
    the report parametric: new brands or report variants are added by inserting
    rows here, not by changing Python.

    Lives in the local (default) DB, since the original solgar_gen schema is
    not reachable from the app's DB connection.
    """

    query_name = models.CharField("Query name", max_length=120, unique=True)
    query_script = models.TextField("Query script")
    description = models.CharField("Description", max_length=255, blank=True)
    is_active = models.BooleanField("Active", default=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    class Meta:
        verbose_name = "DAD query"
        verbose_name_plural = "DAD queries"
        db_table = "intern_sls_dad_query"
        ordering = ["query_name"]

    def __str__(self) -> str:
        """Readable representation."""
        return self.query_name