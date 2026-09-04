"""
Parametrik depo/distributor parser konfigurasyonu.

Java'daki DepoColumnSpec + DepoCityRule + DepoParserConfig siniflarinin
Python portu. Her sirket + islem tipi (SALES/STOCK) icin parse davranisi
bu nesnelerle parametrik tanimlanir; DepoStorageParser motoru calistirir.

Eski koddaki her "xxxSalesParser / xxxStockParser" metodu = bir ParserConfig.
Yeni sirket eklemek = yeni metod yazmak degil, yeni config girmek.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ParserLayout(str, Enum):
    """Excel yerlesim tipi."""
    VERTICAL = "VERTICAL"   # her alan bir kolon (protek, rigla, badm...)
    PIVOT = "PIVOT"         # sehirler kolon basliklarinda (katren, pulse...)
    SPLIT = "SPLIT"         # tek toplam adet, yuzdelerle bolunur (dijibi...)


class MatchType(str, Enum):
    """Sehir eslesme tipi."""
    EQUALS = "EQUALS"
    CONTAINS = "CONTAINS"


@dataclass
class DepoColumnSpec:
    """
    Tek bir cikti alaninin (PRODUCT, CITY, COUNT, INN...) Excel icinde nasil
    bulunacagini tanimlar.

    - keyword varsa: bu metni iceren baslik hucresi aranir, o kolon kullanilir
      (+ column_offset ile kaydirilir).
    - keyword None ise: fixed_value dogrudan ciktiya yazilir (sabit deger).
    - anchor=True olan tek spec, tablonun basladigi satiri belirler
      (baslik satiri + row_offset = ilk veri satiri).
    """
    field: str                       # PRODUCT, CITY, COUNT, CLIENT, INN, SEGMENT...
    keyword: Optional[str] = None    # baslikta aranan metin; None ise fixed
    column_offset: int = 0           # kolon kaydirma (protek -6/-5 gibi)
    row_offset: int = 0              # anchor ise: baslik + row_offset ilk veri
    fixed_value: str = ""            # keyword None ise yazilacak sabit deger
    anchor: bool = False             # veri satiri baslangicini bu mu belirler
    strip_separators: bool = False   # count'tan ondalik/binlik ayrac temizle

    @property
    def is_fixed(self) -> bool:
        return self.keyword is None

    # --- Java'daki statik fabrika metodlarinin karsiligi ---
    @staticmethod
    def of(field_name: str, keyword: str, column_offset: int = 0) -> "DepoColumnSpec":
        """Keyword ile bulunan kolon (opsiyonel kaydirma)."""
        return DepoColumnSpec(field=field_name, keyword=keyword, column_offset=column_offset)

    @staticmethod
    def anchor_spec(field_name: str, keyword: str, column_offset: int, row_offset: int) -> "DepoColumnSpec":
        """Anchor kolon: veri satirinin nerede basladigini belirler."""
        return DepoColumnSpec(
            field=field_name, keyword=keyword, column_offset=column_offset,
            row_offset=row_offset, anchor=True,
        )

    @staticmethod
    def fixed(field_name: str, value: str) -> "DepoColumnSpec":
        """Sabit deger (ornek: CITY = 'Moscow')."""
        return DepoColumnSpec(field=field_name, keyword=None, fixed_value=value)


@dataclass
class DepoCityRule:
    """
    Sehir bazli ozel kurallar (admin panelden eklenir):

    A) MAPPING: ham sehir/adres metnini standart sehre cevirir
       (protek adres -> sehir). remap_city dolu, split=False.
    B) SPLIT: katrenSales mantigi -- bir sehrin adedinin bir kismini baska
       sehre kaydirir. split=True; adet > threshold ise split_percent kadari
       split_city'ye, kalani orijinal sehre.
    """
    source_city: str                       # eslenecek ham metin (harf duyarsiz)
    match_type: MatchType = MatchType.CONTAINS
    remap_city: Optional[str] = None       # mapping hedefi; None ise ham korunur
    split: bool = False
    split_percent: int = 0
    split_threshold: int = 0
    split_city: Optional[str] = None

    @staticmethod
    def map(source_contains: str, standard_city: str) -> "DepoCityRule":
        """Basit mapping: 'Kazan iceren adres' -> 'Kazan'."""
        return DepoCityRule(
            source_city=source_contains, match_type=MatchType.CONTAINS,
            remap_city=standard_city,
        )

    @staticmethod
    def map_exact(source: str, standard_city: str) -> "DepoCityRule":
        """Tam esitlikle mapping."""
        return DepoCityRule(
            source_city=source, match_type=MatchType.EQUALS,
            remap_city=standard_city,
        )

    @staticmethod
    def make_split(source_city: str, threshold: int, percent: int, split_city: str) -> "DepoCityRule":
        """katrenSales tarzi split: Krasnodar, adet>3 ise %30 Rostov'a."""
        return DepoCityRule(
            source_city=source_city, match_type=MatchType.EQUALS,
            split=True, split_percent=percent, split_threshold=threshold,
            split_city=split_city,
        )

    def matches(self, city_raw: Optional[str]) -> bool:
        if not city_raw:
            return False
        c = city_raw.strip()
        if self.match_type == MatchType.EQUALS:
            return c.lower() == self.source_city.lower()
        return self.source_city.lower() in c.lower()


@dataclass
class SplitTarget:
    """SPLIT hedefi: toplam adedin sabit yuzdesini bir sehre yazar."""
    city: str
    percent: int


@dataclass
class DepoParserConfig:
    """
    Bir sirket + islem tipi (SALES/STOCK) icin TUM parse davranisi.
    Admin panelde doldurulur; DepoStorageParser calistirir.
    """
    company: str                              # "KATREN", "PROTEK"...
    operation: str                            # "SALES" | "STOCK"
    layout: ParserLayout = ParserLayout.VERTICAL

    columns: list[DepoColumnSpec] = field(default_factory=list)
    city_rules: list[DepoCityRule] = field(default_factory=list)

    # --- PIVOT alanlari ---
    pivot_product_keyword: Optional[str] = None
    pivot_first_data_column_offset: int = 1
    pivot_first_data_row_offset: int = 1
    pivot_city_row_offset: int = 0

    # --- SPLIT alanlari ---
    split_product_keyword: Optional[str] = None
    split_count_keyword: Optional[str] = None
    split_row_offset: int = 1
    split_count_column_offset: int = 1
    split_targets: list[SplitTarget] = field(default_factory=list)

    # --- varsayilanlar ---
    default_count: str = "0"
    default_amount: str = "0.00"
