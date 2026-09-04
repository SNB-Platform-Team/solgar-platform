"""
Distributor parse config'leri (DepoParserMain.java portu).

Her fonksiyon, bir distributor + islem tipi (SALES/STOCK) icin hazir
DepoParserConfig dondurur. Java'daki DepoParserMain'in birebir karsiligi.

NOT: Bunlar ORNEK/baslangic config'leri. Nihai hedef, bunlarin Django
model + admin panelinde saklanmasi (yonetici formdan girsin). Simdilik
kod icinde tanimli; test + gecis icin.

Legacy parserlar (venta, optima, pulse stock, dijibi sale, vtime stock)
Java'da hala eski yontemde (sheet alan, config degil) -- onlar ayri ele
alinacak, burada YOK.
"""
from __future__ import annotations

from .depo_parser_config import (
    DepoParserConfig, DepoColumnSpec, DepoCityRule, SplitTarget, ParserLayout,
)


# protekStock icin sehir mapping listesi (Java PROTEK_CITIES)
_PROTEK_CITIES = [
    "Казань", "Барнаул", "Самара", "Екатеринбург", "Новосибирск",
    "Волгоград", "Ростов на Дону", "Омск", "Мурманск", "Хабаровск",
    "Владивосток", "Иркутск", "С.- Петербург", "Краснодар", "Пенза",
    "Ставрополь", "Ярославль", "Сургут", "Курск", "Астрахань",
]


# ==================== KATREN (PIVOT + sehir split) ====================
def katren_sale() -> DepoParserConfig:
    c = DepoParserConfig("KATREN", "SALES", layout=ParserLayout.PIVOT)
    c.pivot_product_keyword = "Продажи по системе"
    c.pivot_first_data_column_offset = 1
    c.pivot_first_data_row_offset = 3
    c.pivot_city_row_offset = 2
    c.columns.append(DepoColumnSpec.fixed("CLIENT", ""))
    c.city_rules.append(DepoCityRule.make_split("КРАСНОДАР", 3, 30, "РОСТОВ-НА-ДОНУ"))
    c.city_rules.append(DepoCityRule.make_split("ТЮМЕНЬ", 9, 10, "Сургут"))
    c.city_rules.append(DepoCityRule.make_split("ЧЕЛЯБИНСК", 2, 45, "Екатеринбург"))
    return c


def katren_stock() -> DepoParserConfig:
    c = DepoParserConfig("KATREN", "STOCK", layout=ParserLayout.PIVOT)
    c.pivot_product_keyword = "Поставщик"
    c.pivot_first_data_column_offset = 1
    c.pivot_first_data_row_offset = 4
    c.pivot_city_row_offset = 3
    c.city_rules.append(DepoCityRule.make_split("КРАСНОДАР", 3, 30, "РОСТОВ-НА-ДОНУ"))
    c.city_rules.append(DepoCityRule.make_split("ТЮМЕНЬ", 9, 10, "Сургут"))
    c.city_rules.append(DepoCityRule.make_split("ЧЕЛЯБИНСК", 2, 45, "Екатеринбург"))
    return c


# ==================== PROTEK (VERTICAL) ====================
def protek_sale() -> DepoParserConfig:
    c = DepoParserConfig("PROTEK", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "наименование", 0, 1))
    c.columns.append(DepoColumnSpec.of("CLIENT", "клиент"))
    c.columns.append(DepoColumnSpec.of("LEGALADDRESS", "юр. Адрес"))
    c.columns.append(DepoColumnSpec.of("ACTUALADDRESS", "факт. Адрес"))
    c.columns.append(DepoColumnSpec.of("INN", "ИНН"))
    spec = DepoColumnSpec.of("COUNT", "отгружено")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CITY", "регион"))
    c.columns.append(DepoColumnSpec.of("SEGMENT", "сегмент"))
    return c


def protek_stock() -> DepoParserConfig:
    c = DepoParserConfig("PROTEK", "STOCK", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "наименование", 0, 1))
    c.columns.append(DepoColumnSpec.of("CITY", "склад"))
    c.columns.append(DepoColumnSpec.of("COUNT", "всего"))
    for city in _PROTEK_CITIES:
        c.city_rules.append(DepoCityRule.map(city, city))
    return c


# ==================== DIJIBI (SPLIT) ====================
def dijibi_stock() -> DepoParserConfig:
    c = DepoParserConfig("DIJIBI", "STOCK", layout=ParserLayout.SPLIT)
    c.split_product_keyword = "Наименование (АВЕ; [AHR/GDP])"
    c.split_count_keyword = None
    c.split_count_column_offset = 1
    c.split_row_offset = 1
    c.split_targets.append(SplitTarget("Москва", 95))
    c.split_targets.append(SplitTarget("САНКТ-ПЕТЕРБУРГ", 5))
    return c


# ==================== VITALAIN (SPLIT) ====================
def vitalain_sale() -> DepoParserConfig:
    c = DepoParserConfig("VITALAIN", "SALES", layout=ParserLayout.SPLIT)
    c.split_product_keyword = "Номенклатура, Базовая единица измерения"
    c.split_count_keyword = "Количество (в базовых единицах)"
    c.split_row_offset = 2
    c.split_targets.append(SplitTarget("САМАРА", 90))
    c.split_targets.append(SplitTarget("КАЗАНЬ", 10))
    return c


# ==================== PULSE ====================
def pulse_sale() -> DepoParserConfig:
    c = DepoParserConfig("PULSE", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Номенклатура", 0, 1))
    spec = DepoColumnSpec.of("COUNT", "Количество")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.fixed("CITY", "Москва"))
    return c


# ==================== BADM ====================
def badm_sale() -> DepoParserConfig:
    c = DepoParserConfig("BADM", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Товар", 0, 1))
    c.columns.append(DepoColumnSpec.of("CITY", "Область"))
    c.columns.append(DepoColumnSpec.of("COUNT", "Количество"))
    return c


def badm_stock() -> DepoParserConfig:
    c = DepoParserConfig("BADM", "STOCK", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Товар", 0, 1))
    c.columns.append(DepoColumnSpec.of("CITY", "Филиал"))
    c.columns.append(DepoColumnSpec.of("COUNT", "Количество доступное"))
    return c


# ==================== RIGLA ====================
def rigla_sale() -> DepoParserConfig:
    c = DepoParserConfig("RIGLA", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Наименование препарата", 0, 1))
    c.columns.append(DepoColumnSpec.of("CLIENT", "Поставщик"))
    c.columns.append(DepoColumnSpec.of("ACTUALADDRESS", "Адрес доставки"))
    c.columns.append(DepoColumnSpec.of("INN", "Код АП"))
    spec = DepoColumnSpec.of("COUNT", "Количество")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CITY", "Получатель"))
    return c


def rigla_stock() -> DepoParserConfig:
    c = DepoParserConfig("RIGLA", "STOCK", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Полное название", 0, 1))
    c.columns.append(DepoColumnSpec.of("CLIENT", "Поставщик"))
    c.columns.append(DepoColumnSpec.of("INN", "Код АП"))
    spec = DepoColumnSpec.of("COUNT", "Остатки на")
    spec.strip_separators = True
    c.columns.append(spec)
    return c


# ==================== APTEKA-RU ====================
def apteka_ru_sale() -> DepoParserConfig:
    c = DepoParserConfig("APTEKARU", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Товар", 0, 1))
    c.columns.append(DepoColumnSpec.of("AMOUNT", "Apteka.ru. Товарооборот (без НДС), руб."))
    spec = DepoColumnSpec.of("COUNT", "Apteka.ru. Продажи, шт.")
    spec.strip_separators = True
    c.columns.append(spec)
    return c


# ==================== GRAND KAPITAL ====================
def grand_kapital_sale() -> DepoParserConfig:
    c = DepoParserConfig("GRANDKAPITAL", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "_Название Товара", 0, 1))
    c.columns.append(DepoColumnSpec.of("CLIENT", "Имя Контрагента Краткое"))
    c.columns.append(DepoColumnSpec.of("ACTUALADDRESS", "Адрес Грузополучателя"))
    c.columns.append(DepoColumnSpec.of("INN", "ИНН"))
    spec = DepoColumnSpec.of("COUNT", "Кол-во")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CITY", "Регион"))
    return c


def grand_kapital_stock() -> DepoParserConfig:
    c = DepoParserConfig("GRANDKAPITAL", "STOCK", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Наименование", 0, 1))
    c.columns.append(DepoColumnSpec.of("AMOUNT", "Сумма зак."))
    spec = DepoColumnSpec.of("COUNT", "Остаток")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CITY", "Организация"))
    return c


# ==================== EMITI ====================
def emiti_sale() -> DepoParserConfig:
    c = DepoParserConfig("EMITI", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Товар", 0, 1))
    spec = DepoColumnSpec.of("COUNT", "Продажи, шт.")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CITY", "Отдел"))
    return c


# ==================== MEDSERVIS ====================
def medservis_sale() -> DepoParserConfig:
    c = DepoParserConfig("MEDSERVIS", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("CITY", "Имя 1", 0, 1))
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Краткий текст материала", 0, 1))
    spec = DepoColumnSpec.of("COUNT", "Колво в ЕИ ввода")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CLIENT", "Имя Клиента"))
    return c


def medservis_stock() -> DepoParserConfig:
    c = DepoParserConfig("MEDSERVIS", "STOCK", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("PRODUCT", "Товар", 0, 4))
    c.columns.append(DepoColumnSpec.of("CITY", "Филиал"))
    spec = DepoColumnSpec.of("COUNT", "Конечный остаток")
    spec.strip_separators = True
    c.columns.append(spec)
    return c


# ==================== VTIME ====================
def vtime_sale() -> DepoParserConfig:
    c = DepoParserConfig("VTIME", "SALES", layout=ParserLayout.VERTICAL)
    c.columns.append(DepoColumnSpec.anchor_spec("CITY", "Регион покупателя", 0, 1))
    c.columns.append(DepoColumnSpec.of("PRODUCT", "Модификация"))
    spec = DepoColumnSpec.of("COUNT", "Январь")
    spec.strip_separators = True
    c.columns.append(spec)
    c.columns.append(DepoColumnSpec.of("CLIENT", "Наименование"))
    return c


# get_parser_config'in kullandigi (opsiyonel harita - simdilik dokunulmuyor)
CONFIG_BUILDERS: dict = {}
