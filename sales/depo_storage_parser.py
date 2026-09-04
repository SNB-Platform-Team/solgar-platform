"""
Tum sirket parser'larinin yerine gecen TEK parametrik motor.
Java'daki DepoStorageParser'in Python portu.

Kullanim:
    cfg = load_config(company, operation)   # admin panelden
    rows = DepoStorageParser().parse(sheet, cfg, main_group, v_limit, h_limit)

sheet: satir/kolon okunabilen bir tablo. Burada openpyxl worksheet ya da
2D liste bekleriz; _read() bunu soyutlar. rows: list[dict] (her dict bir satir,
alan -> deger). Java'daki ESIBag yerine list[dict] donuyoruz.
"""
from __future__ import annotations

import math
from typing import Optional

from .depo_parser_config import (
    DepoParserConfig, DepoColumnSpec, DepoCityRule, ParserLayout,
)


class DepoStorageParser:
    """Sirkete ozel HICBIR sey bilmez; tum davranis cfg'den gelir."""

    # ---- hucre okuma (openpyxl worksheet: 1-indexli; biz 0-indexli calisiyoruz) ----
    @staticmethod
    def _read(sheet, col: int, row: int) -> str:
        """Guvenli hucre okuma (0-indexli col/row). Bos -> ''."""
        if col < 0 or row < 0:
            return ""
        try:
            val = sheet.cell(row=row + 1, column=col + 1).value  # openpyxl 1-indexli
        except Exception:
            return ""
        return "" if val is None else str(val)

    @staticmethod
    def _not_empty(s: Optional[str]) -> bool:
        return bool(s) and len(s) > 0

    @staticmethod
    def _strip_separators(count: Optional[str]) -> str:
        """Binlik/ondalik ayraclarini temizler."""
        if count is None:
            return "0"
        if "," in count or "." in count:
            count = count.replace(",", "").replace(".", "")
        return count if len(count) > 0 else "0"

    @staticmethod
    def _parse_int_safe(s: Optional[str]) -> int:
        if not s:
            return 0
        s = s.strip()
        dot = s.find(".")
        if dot >= 0:
            s = s[:dot]
        comma = s.find(",")
        if comma >= 0:
            s = s[:comma]
        if not s:
            return 0
        try:
            return int(s)
        except ValueError:
            return 0

    # ==================================================================
    def parse(self, sheet, cfg: DepoParserConfig, main_group: str,
              vertical_limit: int, horizontal_limit: int) -> list[dict]:
        if cfg.layout == ParserLayout.PIVOT:
            return self._parse_pivot(sheet, cfg, main_group, vertical_limit, horizontal_limit)
        if cfg.layout == ParserLayout.SPLIT:
            return self._parse_split(sheet, cfg, main_group, vertical_limit, horizontal_limit)
        return self._parse_vertical(sheet, cfg, main_group, vertical_limit, horizontal_limit)

    # ==================================================================
    # VERTICAL : her alan bir kolon
    # ==================================================================
    def _parse_vertical(self, sheet, cfg, main_group, v_limit, h_limit) -> list[dict]:
        out: list[dict] = []
        col_index: dict[str, int] = {}
        start_row = 0
        found = False

        for row_no in range(v_limit):
            for col_no in range(h_limit):
                cell = self._read(sheet, col_no, row_no)
                if len(cell) == 0:
                    continue
                for spec in cfg.columns:
                    if spec.is_fixed:
                        continue
                    if spec.keyword in cell:
                        col_index[spec.field] = col_no + spec.column_offset
                        if spec.anchor:
                            start_row = row_no + spec.row_offset
                            found = True
            if found:
                break

        table_index = 0
        for i in range(start_row, v_limit):
            if i <= 0:
                continue
            gate_field = "CITY" if "CITY" in col_index else "PRODUCT"
            gate_col = col_index.get(gate_field)
            if gate_col is None:
                continue
            if not self._not_empty(self._read(sheet, gate_col, i)):
                continue

            city_raw = (self._read(sheet, col_index["CITY"], i).strip()
                        if "CITY" in col_index else None)
            city = self._apply_mapping(cfg, city_raw)

            count = cfg.default_count
            count_col = col_index.get("COUNT")
            if count_col is not None:
                raw = self._read(sheet, count_col, i)
                count = raw if self._not_empty(raw) else cfg.default_count
                if self._spec_strips(cfg, "COUNT"):
                    count = self._strip_separators(count)

            split = self._matching_split(cfg, city_raw)
            if split is not None:
                self._emit_split_row(out, table_index, cfg, col_index, sheet, i, main_group, split, count)
                table_index += 1
                count = self._split_remainder(count, split)

            self._write_row(out, table_index, cfg, col_index, sheet, i, main_group, city, count)
            table_index += 1

        return out

    # ==================================================================
    # PIVOT : sehirler kolon basliklarinda
    # ==================================================================
    def _parse_pivot(self, sheet, cfg, main_group, v_limit, h_limit) -> list[dict]:
        out: list[dict] = []
        product_column = start_column = start_row = city_row = 0
        found = False

        for row_no in range(v_limit):
            for col_no in range(h_limit):
                if cfg.pivot_product_keyword and cfg.pivot_product_keyword in self._read(sheet, col_no, row_no):
                    product_column = col_no
                    start_column = col_no + cfg.pivot_first_data_column_offset
                    start_row = row_no + cfg.pivot_first_data_row_offset
                    city_row = row_no + cfg.pivot_city_row_offset
                    found = True
                    break
            if found:
                break
        if not found:
            return out

        table_index = 0
        for col in range(start_column, h_limit - 1):
            for i in range(start_row, v_limit - 1):
                city_raw = self._read(sheet, col, city_row)
                if not self._not_empty(city_raw):
                    continue
                city = self._apply_mapping(cfg, city_raw)
                product = self._read(sheet, product_column, i)
                count = self._read(sheet, col, i)
                if not self._not_empty(count):
                    count = cfg.default_count
                if self._spec_strips(cfg, "COUNT"):
                    count = self._strip_separators(count)

                split = self._matching_split(cfg, city_raw)
                if split is not None:
                    part = self._split_share(count, split)
                    if part != "0":
                        self._put_row(out, table_index, cfg, main_group, split.split_city, product, part)
                        table_index += 1
                    count = self._split_remainder(count, split)

                self._put_row(out, table_index, cfg, main_group, city, product, count)
                table_index += 1
        return out

    # ==================================================================
    # SPLIT : tek toplam adet, sabit yuzdelerle bolunur
    # ==================================================================
    def _parse_split(self, sheet, cfg, main_group, v_limit, h_limit) -> list[dict]:
        out: list[dict] = []
        product_column = count_column = start_row = 0
        found = False

        for row_no in range(v_limit):
            for col_no in range(h_limit):
                cell = self._read(sheet, col_no, row_no)
                if cfg.split_product_keyword and cfg.split_product_keyword in cell:
                    product_column = col_no
                    start_row = row_no + cfg.split_row_offset
                    if cfg.split_count_keyword is None:
                        count_column = col_no + cfg.split_count_column_offset
                        found = True
                        break
                if cfg.split_count_keyword and cfg.split_count_keyword in cell:
                    count_column = col_no
                    found = True
                    break
            if found:
                break
        if not found:
            return out

        table_index = 0
        for i in range(start_row, v_limit - 1):
            if i <= 0:
                continue
            product = self._read(sheet, product_column, i)
            if not self._not_empty(product):
                continue
            count_str = self._read(sheet, count_column, i)
            if not self._not_empty(count_str):
                continue

            total = self._parse_int_safe(count_str)
            assigned = 0
            for t in range(1, len(cfg.split_targets)):
                tgt = cfg.split_targets[t]
                part = round((total / 100.0) * tgt.percent)
                assigned += part
                self._put_row(out, table_index, cfg, main_group, tgt.city, product, str(part))
                table_index += 1
            if cfg.split_targets:
                main = cfg.split_targets[0]
                self._put_row(out, table_index, cfg, main_group, main.city, product, str(total - assigned))
                table_index += 1
        return out

    # ---------------------------------------------------------------------
    # Yardimcilar
    # ---------------------------------------------------------------------
    def _write_row(self, out, idx, cfg, col_index, sheet, row, main_group, city, count):
        rec = {}
        for spec in cfg.columns:
            if spec.is_fixed:
                value = spec.fixed_value
            elif spec.field == "CITY":
                value = city
            elif spec.field == "COUNT":
                value = count
            else:
                col = col_index.get(spec.field)
                value = "" if col is None else self._read(sheet, col, row)
            rec[spec.field] = value
        self._ensure_common(rec, cfg, main_group)
        out.append(rec)

    def _emit_split_row(self, out, idx, cfg, col_index, sheet, row, main_group, split, count):
        share = self._split_share(count, split)
        self._write_row(out, idx, cfg, col_index, sheet, row, main_group, split.split_city, share)

    def _put_row(self, out, idx, cfg, main_group, city, product, count):
        rec = {"CITY": city, "PRODUCT": product or "", "COUNT": count}
        for spec in cfg.columns:
            if spec.is_fixed and spec.field not in ("CITY", "PRODUCT", "COUNT"):
                rec[spec.field] = spec.fixed_value
        self._ensure_common(rec, cfg, main_group)
        out.append(rec)

    def _ensure_common(self, rec, cfg, main_group):
        rec["AMOUNT"] = cfg.default_amount
        rec["MAINGROUP"] = main_group

    def _apply_mapping(self, cfg, city_raw):
        if city_raw is None:
            return None
        for r in cfg.city_rules:
            if not r.split and r.remap_city is not None and r.matches(city_raw):
                return r.remap_city
        return city_raw

    def _matching_split(self, cfg, city_raw):
        if city_raw is None:
            return None
        for r in cfg.city_rules:
            if r.split and r.matches(city_raw):
                return r
        return None

    def _split_share(self, count, rule):
        c = self._parse_int_safe(count)
        if c > rule.split_threshold:
            return str(math.ceil((c * rule.split_percent) / 100.0))
        return "0"

    def _split_remainder(self, count, rule):
        c = self._parse_int_safe(count)
        if c > rule.split_threshold:
            share = math.ceil((c * rule.split_percent) / 100.0)
            return str(c - share)
        return count

    def _spec_strips(self, cfg, field_name):
        return any(s.field == field_name and s.strip_separators for s in cfg.columns)
