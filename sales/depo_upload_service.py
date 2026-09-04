"""
Depo/distributor Excel upload is mantigi (service layer).

Java'daki StorageSalesStockUpload'in Swing arayuzu HARIC is mantigi:
  - dosya adindan + islem tipinden config sec (get_parser_config)
  - DepoStorageParser ile parse et
  - her satiri isle: marka ayrimi (SL/BN/OS), count/amount temizle
  - marka bazli toplamlar
  - onizleme satirlari (list[dict]) + ozet dondur

React upload ekrani bunu preview olarak cagirir; save ayrica kaydeder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .depo_storage_parser import DepoStorageParser
from .depo_parser_config import DepoParserConfig
from . import depo_configs  # her distributor'un hazir config'i (Java DepoParserMain portu)


# ---- Java parseCount / parseAmount karsiligi ----
def parse_count(count_str: Optional[str]) -> int:
    """Count'u int'e cevir (ilk ondalik/virgulden kes, bosluklari sil)."""
    if not count_str:
        return 0
    clean = re.split(r"[.,]", count_str)[0]
    clean = re.sub(r"\s+", "", clean)
    if not clean:
        return 0
    try:
        return max(0, int(clean))
    except ValueError:
        return 0


def parse_amount(amount_str: Optional[str]) -> float:
    """Amount'u float'a cevir (bosluk sil, virgul -> nokta)."""
    if not amount_str or not amount_str.strip() or amount_str.strip() == ",00":
        return 0.0
    clean = re.sub(r"\s+", "", amount_str).replace(" ", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def get_parser_config(file_name: str, is_sales: bool) -> Optional[DepoParserConfig]:
    """
    Dosya adindan + islem tipinden dogru config'i sec.
    Java'daki getParserConfig eslesme tablosunun portu.
    Dosya adi buyuk harfe cevrilmis gelir.
    """
    fn = (file_name or "").upper()
    cfg_map = depo_configs.CONFIG_BUILDERS  # {(anahtar, is_sales|None): builder}

    # Sirali kontrol (Java'daki if zinciri gibi)
    if "КАТРЕН" in fn:
        return depo_configs.katren_sale() if is_sales else depo_configs.katren_stock()
    if "ПРОТЕК" in fn:
        return depo_configs.protek_sale() if is_sales else depo_configs.protek_stock()
    if "ПУЛЬС" in fn and is_sales:
        return depo_configs.pulse_sale()
    if "БАДМ" in fn:
        return depo_configs.badm_sale() if is_sales else depo_configs.badm_stock()
    if "ВИТАЛАЙНСАМАРА" in fn and is_sales:
        return depo_configs.vitalain_sale()
    if "РИГЛА" in fn:
        return depo_configs.rigla_sale() if is_sales else depo_configs.rigla_stock()
    if "APTEKA-RU" in fn and is_sales:
        return depo_configs.apteka_ru_sale()
    if "ГРАНД КАПИТАЛ" in fn:
        return depo_configs.grand_kapital_sale() if is_sales else depo_configs.grand_kapital_stock()
    if "MEDSERVIS" in fn:
        return depo_configs.medservis_sale() if is_sales else depo_configs.medservis_stock()
    if "VTIME" in fn and is_sales:
        return depo_configs.vtime_sale()
    return None


def classify_brand(product: str) -> str:
    """
    Urun adindan marka/tip belirle (Java'daki mantik):
      БАУНТИ/BOUNTY/НЭЙЧЕС -> BN
      ОСТЕО/OSTEO          -> OS
      diger                -> SL (Solgar)
    """
    p = (product or "").upper()
    if "БАУНТИ" in p or "BOUNTY" in p or "НЭЙЧЕС" in p:
        return "BN"
    if "ОСТЕО" in p or "OSTEO" in p:
        return "OS"
    return "SL"


@dataclass
class DepoPreviewResult:
    """Onizleme sonucu: satirlar + marka bazli ozet."""
    rows: list[dict] = field(default_factory=list)
    stock_sales_type: str = ""          # SALES | STOCK
    total_count_solgar: int = 0
    total_amount_solgar: float = 0.0
    total_count_bounty: int = 0
    total_amount_bounty: float = 0.0
    error: str = ""


class DepoUploadService:
    """StorageSalesStockUpload is mantigi (arayuzsuz)."""

    def preview(self, sheet, file_name: str, distributor: str,
                main_group: str, v_limit: int, h_limit: int) -> DepoPreviewResult:
        """
        Excel'i parse edip onizleme satirlarini + marka ozetini dondur.
        sheet: openpyxl worksheet. file_name: yuklenen dosyanin adi (config secimi icin).
        distributor: secili distributor (dogrulama). main_group: urun ana grubu.
        """
        result = DepoPreviewResult()
        fn = (file_name or "").upper()

        # Dosya adi secilen distributor'u icermeli (Java kontrolu)
        if distributor and distributor.upper() not in fn:
            result.error = "Dosya adi secilen distributor ile eslesmiyor."
            return result

        # SALES / STOCK: dosya adinda "ПРОДАЖИ" varsa satis
        stock_sales_type = "SALES" if "ПРОДАЖИ" in fn else "STOCK"
        is_sales = stock_sales_type == "SALES"
        result.stock_sales_type = stock_sales_type

        cfg = get_parser_config(fn, is_sales)
        if cfg is None:
            result.error = f"'{file_name}' icin parse konfigurasyonu bulunamadi."
            return result

        parsed = DepoStorageParser().parse(sheet, cfg, main_group, v_limit, h_limit)

        rows = []
        for idx, rec in enumerate(parsed):
            product = rec.get("PRODUCT", "") or ""
            count = parse_count(rec.get("COUNT"))
            amount = parse_amount(rec.get("AMOUNT"))
            product_type = classify_brand(product)

            if product_type in ("BN", "OS"):
                result.total_amount_bounty += amount
                result.total_count_bounty += count
            else:
                result.total_amount_solgar += amount
                result.total_count_solgar += count

            rows.append({
                "index": idx + 1,
                "main_group": rec.get("MAINGROUP", ""),
                "type": stock_sales_type,
                "city": rec.get("CITY", ""),
                "product": product,
                "product_type": product_type,
                "count": count,
                "amount": round(amount, 2),
                "client": (rec.get("CLIENT", "") or "").strip(),
                "legal_address": (rec.get("LEGALADDRESS", "") or "").strip(),
                "actual_address": (rec.get("ACTUALADDRESS", "") or "").strip(),
                "inn": (rec.get("INN", "") or "").strip(),
                "segment": (rec.get("SEGMENT", "") or "").strip(),
            })

        result.rows = rows
        return result
