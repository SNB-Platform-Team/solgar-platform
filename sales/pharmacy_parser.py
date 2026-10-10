"""
Eczane zinciri Excel parser'i - parametrik motor + config yapisi.
Java Companies.UkVerticalSimpleParser'in BIREBIR Python portu + parametrik config.

Legacy 170 hardcoded parser -> parametrik config.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Layout(str, Enum):
    VERTICAL = "VERTICAL"
    PIVOT = "PIVOT"


class ExtractMode(str, Enum):
    CONTAINS_FIXED = "CONTAINS_FIXED"
    BEFORE_MARKER = "BEFORE_MARKER"
    AFTER_MARKER = "AFTER_MARKER"


@dataclass
class ColumnSpec:
    field: str
    keyword: Optional[str] = None
    column_offset: int = 0
    row_offset: int = 0
    fixed_value: str = ""
    anchor: bool = False
    strip_separators: bool = False
    match_exact: bool = True

    @property
    def is_fixed(self) -> bool:
        return self.keyword is None

    @staticmethod
    def of(field_name, keyword, column_offset=0, match_exact=True):
        return ColumnSpec(field=field_name, keyword=keyword,
                          column_offset=column_offset, match_exact=match_exact)

    @staticmethod
    def anchor_spec(field_name, keyword, row_offset=1, match_exact=True):
        return ColumnSpec(field=field_name, keyword=keyword, row_offset=row_offset,
                          anchor=True, match_exact=match_exact)

    @staticmethod
    def fixed(field_name, value):
        return ColumnSpec(field=field_name, keyword=None, fixed_value=value)

    @staticmethod
    def count(keyword, match_exact=True):
        return ColumnSpec(field="COUNT", keyword=keyword, strip_separators=False,
                          match_exact=match_exact)


@dataclass
class ExtractRule:
    source_field: str
    target_field: str
    mode: ExtractMode
    marker: str
    fixed_result: str = ""
    marker_offset: int = 0
    remove_from_source: bool = True
    fallback: str = ""

    @staticmethod
    def contains_fixed(source, target, marker, fixed_result):
        return ExtractRule(source, target, ExtractMode.CONTAINS_FIXED, marker,
                          fixed_result=fixed_result, remove_from_source=False)

    @staticmethod
    def before_marker(source, target, marker, fallback=""):
        return ExtractRule(source, target, ExtractMode.BEFORE_MARKER, marker,
                          fallback=fallback)

    @staticmethod
    def after_marker(source, target, marker, marker_offset=0):
        return ExtractRule(source, target, ExtractMode.AFTER_MARKER, marker,
                          marker_offset=marker_offset)


@dataclass
class PharmacyConfig:
    """
    Bir eczane zinciri config'i. SimpleVertical icin kolon isimleri +
    last_column (Java prmLastColumn - baslik aramayi durdurur, tekrar eden
    kolonlarda dogru occurrence icin kritik).
    """
    company: str
    operation: str = "SALES"
    layout: Layout = Layout.VERTICAL
    # SimpleVertical alanlari (Java UkVerticalSimpleParser parametreleri)
    product: str = ""
    pharmacy: str = ""       # prmAddress
    count: str = ""
    amount: str = ""
    pharmacy_no: str = ""
    city: str = ""
    remains_count: str = ""
    remains_amount: str = ""
    last_column: str = ""    # prmLastColumn - baslik taramasini durdurur
    extract_rules: list[ExtractRule] = field(default_factory=list)

    def rule(self, r: ExtractRule) -> "PharmacyConfig":
        self.extract_rules.append(r)
        return self


class PharmacyParser:
    """Java UkVerticalSimpleParser'in birebir portu (parametrik)."""

    @staticmethod
    def _read(sheet, col: int, row: int) -> str:
        if col < 0 or row < 0:
            return ""
        try:
            val = sheet.cell(row=row + 1, column=col + 1).value
        except Exception:
            return ""
        if val is None:
            return ""
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val)

    @staticmethod
    def _ne(s) -> bool:
        return s is not None and len(s.strip()) > 0

    @staticmethod
    def _hmatch(cell, spec):
        """Baslik eslesmesi: spec '|' ile ayrilmis alternatifler icerebilir."""
        if not spec:
            return False
        c = cell.lower()
        return any(c == alt.strip().lower() for alt in spec.split("|") if alt.strip())

    def parse(self, sheet, cfg: PharmacyConfig, main_group: str,
              v_limit: int, h_limit: int) -> list[dict]:
        """
        Java UkVerticalSimpleParser mantigi birebir:
        1. Basliklari tara (equalsIgnoreCase), her alanin kolonunu bul.
           Tekrar eden basliklarda SON eslesen kalir (Java gibi).
           last_column bulununca taramayi DURDUR.
        2. startOfRow'dan itibaren her satiri al (gate yok).
        """
        p = cfg
        start_row = 0
        col = {"product": 0, "pharmacy": 0, "count": 0, "amount": 0,
               "pharmacy_no": 0, "city": 0, "remains_count": 0, "remains_amount": 0}
        break_for = False

        for row_no in range(v_limit):
            if break_for:
                break
            for col_no in range(h_limit):
                cell = self._read(sheet, col_no, row_no).strip()
                # Java: equalsIgnoreCase (tam esitlik)
                if self._hmatch(cell, p.product):
                    col["product"] = col_no
                    start_row = row_no + 1
                if self._hmatch(cell, p.pharmacy):
                    col["pharmacy"] = col_no
                if self._hmatch(cell, p.count):
                    col["count"] = col_no
                if self._hmatch(cell, p.amount):
                    col["amount"] = col_no
                if self._hmatch(cell, p.pharmacy_no):
                    col["pharmacy_no"] = col_no
                if self._hmatch(cell, p.city):
                    col["city"] = col_no
                if self._hmatch(cell, p.remains_count):
                    col["remains_count"] = col_no
                if self._hmatch(cell, p.remains_amount):
                    col["remains_amount"] = col_no
                # last_column bulununca dur (Java breakFor)
                if self._hmatch(cell, p.last_column):
                    break_for = True
                    break

        out = []
        for i in range(start_row, v_limit):
            product_val = self._read(sheet, col["product"], i)
            # Product bos ya da baslik kalintisi ise atla (Java pratikte bos satir uretir,
            # ama anlamsiz; product dolu olmali).
            if not self._ne(product_val):
                continue
            rec = {}
            rec["PRODUCT"] = product_val

            if p.pharmacy:
                v = self._read(sheet, col["pharmacy"], i)
                rec["SALESREADER"] = v if self._ne(v) else ""
                rec["PHARMACY"] = v if self._ne(v) else ""
            else:
                rec["SALESREADER"] = ""
                rec["PHARMACY"] = ""

            if p.count:
                v = self._read(sheet, col["count"], i)
                rec["COUNT"] = v if self._ne(v) else "0"
            else:
                rec["COUNT"] = "0"

            if p.amount:
                v = self._read(sheet, col["amount"], i)
                rec["AMOUNT"] = v if self._ne(v) else "0.00"
            else:
                rec["AMOUNT"] = "0.00"

            if p.pharmacy_no:
                v = self._read(sheet, col["pharmacy_no"], i)
                rec["APTEKNO"] = v if self._ne(v) else ""
            else:
                rec["APTEKNO"] = ""

            if p.city:
                v = self._read(sheet, col["city"], i)
                rec["CITY"] = v if self._ne(v) else ""
            else:
                rec["CITY"] = ""

            if p.remains_count:
                v = self._read(sheet, col["remains_count"], i)
                rec["REMAINING_COUNT"] = v if self._ne(v) else "0"
            else:
                rec["REMAINING_COUNT"] = "0"

            if p.remains_amount:
                v = self._read(sheet, col["remains_amount"], i)
                rec["REMAINING_AMOUNT"] = v if self._ne(v) else "0.00"
            else:
                rec["REMAINING_AMOUNT"] = "0.00"

            rec["SUBGROUP"] = main_group
            rec["MAINGROUP"] = main_group

            self._apply_extract(rec, cfg, main_group)
            out.append(rec)
        return out

    def _apply_extract(self, rec, cfg, main_group):
        for r in cfg.extract_rules:
            source = rec.get(r.source_field, "") or ""
            if r.mode == ExtractMode.CONTAINS_FIXED:
                if r.marker in source:
                    rec[r.target_field] = r.fixed_result
            elif r.mode == ExtractMode.BEFORE_MARKER:
                idx = source.find(r.marker)
                if idx > 0:
                    part = source[:idx]
                    rec[r.target_field] = part
                    if r.remove_from_source:
                        rec[r.source_field] = source.replace(part, "")
                else:
                    fb = main_group if r.fallback == "$MAINGROUP" else r.fallback
                    if fb:
                        rec[r.target_field] = fb
            elif r.mode == ExtractMode.AFTER_MARKER:
                idx = source.find(r.marker)
                if idx >= 0:
                    part = source[idx + r.marker_offset:]
                    rec[r.target_field] = part
                    if r.remove_from_source:
                        rec[r.source_field] = source.replace(part, "")


# ==================== EK MOTORLAR (Generic, Nested, Horizontal, Special) ====================

class ExtractMode2:
    CONTAINS_FIXED = "CONTAINS_FIXED"
    BEFORE_MARKER = "BEFORE_MARKER"
    AFTER_MARKER = "AFTER_MARKER"


@dataclass
class ExtractRule2:
    """String extraction (PHARMACY'den SUBGROUP/APTEKNO çıkarma)."""
    source: str
    target: str
    mode: str
    marker: str
    fixed_result: str = ""
    offset: int = 0
    remove: bool = True
    fallback: str = ""


@dataclass
class GenericConfig:
    """Generic/Special config (contains eşleşme + opsiyonel extract rules)."""
    company: str
    product: str = ""
    pharmacy: str = ""
    count: str = ""
    amount: str = ""
    pharmacy_no: str = ""
    city: str = ""
    rem_count: str = ""
    rem_amount: str = ""
    last_column: str = ""
    extract_rules: list = field(default_factory=list)


@dataclass
class NestedConfig:
    """İç içe (nested) config - ürün/eczane işaretleri."""
    company: str
    product: str = ""
    count: str = ""
    amount: str = ""
    pharmacy_no: str = ""
    city: str = ""
    last_column: str = ""
    pharmacy_markers: list = field(default_factory=lambda: ["Аптека", "Склад", "фарм"])
    product_markers: list = field(default_factory=lambda: ["Солгар", "СОЛГАР", "Solgar"])
    product_starts_with: str = ""


@dataclass
class HorizontalConfig:
    """Horizontal (pivot) config."""
    company: str
    product_keyword: str = ""
    start_column: int = 0
    pharmacy_row_offset: int = 0


def _read2(sheet, col, row):
    if col < 0 or row < 0:
        return ""
    try:
        val = sheet.cell(row=row + 1, column=col + 1).value
    except Exception:
        return ""
    if val is None:
        return ""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val)


def _ne2(s):
    return bool(s) and len(str(s).strip()) > 0


def _apply_extract2(rec, rules, main_group):
    for r in rules:
        source = rec.get(r.source, "") or ""
        if r.mode == ExtractMode2.CONTAINS_FIXED:
            if r.marker in source:
                rec[r.target] = r.fixed_result
        elif r.mode == ExtractMode2.BEFORE_MARKER:
            idx = source.find(r.marker)
            if idx > 0:
                part = source[:idx]
                rec[r.target] = part.strip()
                if r.remove:
                    rec[r.source] = source.replace(part, "")
            else:
                fb = main_group if r.fallback == "$MAINGROUP" else r.fallback
                if fb:
                    rec[r.target] = fb
        elif r.mode == ExtractMode2.AFTER_MARKER:
            idx = source.find(r.marker)
            if idx >= 0:
                part = source[idx + r.offset:]
                rec[r.target] = part.strip()
                if r.remove:
                    rec[r.source] = source.replace(part, "")


class GenericParser:
    """Contains eşleşmeli motor (SIMPLE_LIKE + Special). extract_rules varsa uygular."""
    def parse(self, sheet, p, main_group, v_limit, h_limit):
        start_row = 0
        cols = {"product":0,"pharmacy":0,"count":0,"amount":0,"pharmacy_no":0,"city":0,"rem_count":0,"rem_amount":0}
        fields = [("product",p.product),("pharmacy",p.pharmacy),("count",p.count),("amount",p.amount),
                  ("pharmacy_no",p.pharmacy_no),("city",p.city),("rem_count",p.rem_count),("rem_amount",p.rem_amount)]
        brk = False
        for row_no in range(v_limit):
            if brk: break
            for col_no in range(h_limit):
                cell = _read2(sheet, col_no, row_no)
                if not cell: continue
                for key, kw in fields:
                    if kw and kw in cell:
                        cols[key] = col_no
                        if key == "product":
                            start_row = row_no + 1
                if p.last_column and p.last_column in cell:
                    brk = True; break
        out = []
        for i in range(start_row, v_limit):
            product = _read2(sheet, cols["product"], i)
            if not _ne2(product): continue
            rec = {"PRODUCT": product}
            ph = _read2(sheet, cols["pharmacy"], i) if p.pharmacy else ""
            rec["PHARMACY"] = ph; rec["SALESREADER"] = ph
            rec["COUNT"] = _read2(sheet,cols["count"],i) if p.count and _ne2(_read2(sheet,cols["count"],i)) else "0"
            rec["AMOUNT"] = _read2(sheet,cols["amount"],i) if p.amount and _ne2(_read2(sheet,cols["amount"],i)) else "0.00"
            rec["APTEKNO"] = _read2(sheet,cols["pharmacy_no"],i) if p.pharmacy_no else ""
            rec["CITY"] = _read2(sheet,cols["city"],i) if p.city else ""
            rec["REMAINING_COUNT"] = _read2(sheet,cols["rem_count"],i) if p.rem_count and _ne2(_read2(sheet,cols["rem_count"],i)) else "0"
            rec["REMAINING_AMOUNT"] = _read2(sheet,cols["rem_amount"],i) if p.rem_amount and _ne2(_read2(sheet,cols["rem_amount"],i)) else "0.00"
            rec["SUBGROUP"] = main_group; rec["MAINGROUP"] = main_group
            if p.extract_rules:
                _apply_extract2(rec, p.extract_rules, main_group)
            out.append(rec)
        return out


class NestedParser:
    """İç içe motor (eczane/ürün satırları aynı kolonda)."""
    def _is_ph(self, s, p):
        return any(m in s for m in p.pharmacy_markers)
    def _is_pr(self, s, p):
        if p.product_starts_with and s[:len(p.product_starts_with)] == p.product_starts_with:
            return True
        return any(m in s for m in p.product_markers)
    def parse(self, sheet, p, main_group, v_limit, h_limit):
        start_row = 0; c_prod = 0; c_count = 1; c_amount = 2; c_pno = 0; c_city = 0
        brk = False
        for row_no in range(v_limit):
            if brk: break
            for col_no in range(h_limit):
                cell = _read2(sheet, col_no, row_no).strip()
                if not cell: continue
                if p.product and cell.lower() == p.product.lower():
                    c_prod = col_no; start_row = row_no + 1
                if p.count and cell.lower() == p.count.lower(): c_count = col_no
                if p.amount and cell.lower() == p.amount.lower(): c_amount = col_no
                if p.last_column and cell.lower() == p.last_column.lower():
                    brk = True; break
        pharmacy = ""; out = []
        for i in range(start_row, v_limit):
            cell = _read2(sheet, c_prod, i)
            if not _ne2(cell): continue
            if self._is_ph(cell, p):
                pharmacy = cell
            elif self._is_pr(cell, p):
                v = _read2(sheet, c_count, i)
                out.append({
                    "PRODUCT": cell, "PHARMACY": pharmacy, "SALESREADER": pharmacy,
                    "COUNT": v if _ne2(v) else "0",
                    "AMOUNT": _read2(sheet,c_amount,i) if _ne2(_read2(sheet,c_amount,i)) else "0.00",
                    "APTEKNO": _read2(sheet,c_pno,i) if p.pharmacy_no else "",
                    "CITY": _read2(sheet,c_city,i) if p.city else "",
                    "SUBGROUP": main_group, "MAINGROUP": main_group,
                })
        return out


class AvromedParser:
    """Avromed/Buta transpoze pivot motoru.
    - Satir 0: aptek adlari (her aptek 4 sutunluk blok, blok basi ilk sutunda)
    - Satir 1: alt-basliklar (Sales QTY / Sales Amount / RRP / Depo stock)
    - Satir 2+: A sutununda urun, her blokta +0=adet(QTY), +1=tutar(Amount)
    Aptekler sutun 1'den baslar, 4'er 4'er. A sutunu (col 0) urun adi.
    """
    PRODUCT_COL = 0
    FIRST_APTEK_COL = 1
    BLOCK = 4
    DATA_START_ROW = 2

    def parse(self, sheet, p, main_group, v_limit, h_limit):
        out = []
        # Aptek bloklarini tespit et: satir 0'da ismi dolu olan sutunlar
        aptek_cols = []  # (col, aptek_adi)
        last_name = ""
        col = self.FIRST_APTEK_COL
        while col < h_limit:
            name = _read2(sheet, col, 0).strip()
            if _ne2(name):
                last_name = name
                aptek_cols.append((col, name))
            col += self.BLOCK
        # Her urun satiri icin her aptek bloguna bak
        for i in range(self.DATA_START_ROW, v_limit):
            product = _read2(sheet, self.PRODUCT_COL, i).strip()
            if not _ne2(product):
                continue
            for acol, aname in aptek_cols:
                qty = _read2(sheet, acol, i)          # +0 = adet
                amount = _read2(sheet, acol + 1, i)   # +1 = tutar
                # sadece satisi olan (adet dolu) kayitlari al
                if not _ne2(qty):
                    continue
                out.append({
                    "PRODUCT": product, "PHARMACY": aname, "SALESREADER": aname,
                    "APTEKNO": "", "CITY": "",
                    "COUNT": qty,
                    "AMOUNT": amount if _ne2(amount) else "0.00",
                    "REMAINING_COUNT": "0", "REMAINING_AMOUNT": "0.00",
                    "SUBGROUP": main_group, "MAINGROUP": main_group,
                })
        return out


class NestedKgParser:
    """Tek sutun (A) baslik+alt satir hiyerarsisi, deger B sutununda (adet).
    cfg beklenen alanlar (dict):
      mode: 'pharmacy_header' | 'product_header'
      aptek_marker: aptek satirini taniyan metin (orn 'Аптека' veya 'Неман')
      data_start: ilk veri satiri (baslik satir sayisi)
      count_col: adet sutunu index (varsayilan 1)
      name_col: ad sutunu index (varsayilan 0)
    """
    def parse(self, sheet, cfg, main_group, v_limit, h_limit):
        mode = cfg.get("mode", "pharmacy_header")
        marker = cfg.get("aptek_marker", "Аптека")
        start = cfg.get("data_start", 2)
        ccol = cfg.get("count_col", 1)
        ncol = cfg.get("name_col", 0)
        out = []
        cur_aptek = ""
        cur_product = ""
        for i in range(start, v_limit):
            name = _read2(sheet, ncol, i).strip()
            if not _ne2(name):
                continue
            is_aptek = marker.lower() in name.lower()
            val = _read2(sheet, ccol, i)
            if mode == "pharmacy_header":
                # aptek satiri -> aktif aptek; diger -> urun kaydi
                if is_aptek:
                    cur_aptek = name
                else:
                    out.append(self._rec(name, cur_aptek, val, main_group))
            else:  # product_header: urun satiri -> aktif urun; aptek satiri -> kayit
                if is_aptek:
                    out.append(self._rec(cur_product, name, val, main_group))
                else:
                    cur_product = name
        return out

    @staticmethod
    def _rec(product, pharmacy, cnt, mg):
        return {
            "PRODUCT": product, "PHARMACY": pharmacy, "SALESREADER": pharmacy,
            "APTEKNO": "", "CITY": "",
            "COUNT": cnt if _ne2(cnt) else "0",
            "AMOUNT": "0.00", "REMAINING_COUNT": "0", "REMAINING_AMOUNT": "0.00",
            "SUBGROUP": mg, "MAINGROUP": mg,
        }


class MatrixParser:
    """Pivot/matris motoru. cfg (dict):
      product_axis: 'col' (urun sol sutunda) | 'row' (urun ust satirda)
      product_index: urun ekseninin sabit index'i (col veya row no)
      aptek_index: aptek ekseninin sabit index'i
      data_start_row, data_start_col: deger matrisinin basladigi yer
      skip_last_col / skip_last_row: True ise son (Itog/toplam) atlanir
    """
    def parse(self, sheet, cfg, main_group, v_limit, h_limit):
        pax = cfg.get("product_axis", "col")
        pidx = cfg.get("product_index", 0)
        aidx = cfg.get("aptek_index", 0)
        dsr = cfg.get("data_start_row", 2)
        dsc = cfg.get("data_start_col", 1)
        skip_last_col = cfg.get("skip_last_col", False)
        skip_last_row = cfg.get("skip_last_row", False)
        out = []
        rmax = v_limit - (1 if skip_last_row else 0)
        cmax = h_limit - (1 if skip_last_col else 0)
        if pax == "col":
            # urun = sol sutun (pidx) boyunca satirlar; aptek = ust satir (aidx) boyunca sutunlar
            for i in range(dsr, rmax):
                product = _read2(sheet, pidx, i).strip()
                if not _ne2(product):
                    continue
                for j in range(dsc, cmax):
                    aptek = _read2(sheet, j, aidx).strip()
                    if not _ne2(aptek):
                        continue
                    val = _read2(sheet, j, i)
                    if not _ne2(val):
                        continue
                    out.append(self._rec(product, aptek, val, main_group))
        else:
            # urun = ust satir (pidx) boyunca sutunlar; aptek = sol sutun (aidx) boyunca satirlar
            for j in range(dsc, cmax):
                product = _read2(sheet, j, pidx).strip()
                if not _ne2(product):
                    continue
                for i in range(dsr, rmax):
                    aptek = _read2(sheet, aidx, i).strip()
                    if not _ne2(aptek):
                        continue
                    val = _read2(sheet, j, i)
                    if not _ne2(val):
                        continue
                    out.append(self._rec(product, aptek, val, main_group))
        return out

    @staticmethod
    def _rec(product, pharmacy, cnt, mg):
        return {
            "PRODUCT": product, "PHARMACY": pharmacy, "SALESREADER": pharmacy,
            "APTEKNO": "", "CITY": "",
            "COUNT": cnt if _ne2(cnt) else "0",
            "AMOUNT": "0.00", "REMAINING_COUNT": "0", "REMAINING_AMOUNT": "0.00",
            "SUBGROUP": mg, "MAINGROUP": mg,
        }


class HorizontalParser:
    """Pivot motor (ürün satırda, eczane kolonda)."""
    def parse(self, sheet, p, main_group, v_limit, h_limit):
        start_row = 0; prod_col = 0; ph_row = 0; brk = False
        for row_no in range(v_limit):
            if brk: break
            for col_no in range(h_limit):
                cell = _read2(sheet, col_no, row_no)
                if p.product_keyword and p.product_keyword in cell:
                    start_row = row_no + 1; prod_col = col_no
                    ph_row = row_no + p.pharmacy_row_offset
                    brk = True; break
        start_col = p.start_column if p.start_column > 0 else prod_col + 1
        out = []
        col = start_col
        while col < h_limit - 1:
            ph_name = _read2(sheet, col, ph_row)
            if _ne2(ph_name):
                for i in range(start_row, v_limit - 1):
                    prod = _read2(sheet, prod_col, i)
                    if len(prod) > 5:
                        cnt = _read2(sheet, col, i)
                        out.append({
                            "PHARMACY": ph_name, "SALESREADER": ph_name, "APTEKNO": "",
                            "PRODUCT": prod, "COUNT": cnt if _ne2(cnt) else "0",
                            "AMOUNT": "0.00", "CITY": "",
                            "SUBGROUP": main_group, "MAINGROUP": main_group,
                        })
            col += 1
        return out
