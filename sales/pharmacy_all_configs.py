"""
Tum eczane zinciri config'leri - 5 motor icin.
Java'dan Python'a tasindi. get_config(chain) uygun (config, motor_tipi) doner.
"""
from .pharmacy_parser import (
    GenericConfig, NestedConfig, HorizontalConfig, ExtractRule2, ExtractMode2,
    PharmacyParser, GenericParser, NestedParser, HorizontalParser,
)
from .pharmacy_simple_configs import SIMPLE_CONFIGS

# ---- GENERIC (contains) - 124 SIMPLE_LIKE ----
GENERIC = {}
def _g(name, c):
    GENERIC[name.upper()] = GenericConfig(
        company=name, product=c.get("product",""), pharmacy=c.get("pharmacy",""),
        count=c.get("count",""), amount=c.get("amount",""),
        pharmacy_no=c.get("pharmacyNo",""), city=c.get("city",""),
        rem_count=c.get("remCount",""), rem_amount=c.get("remAmount",""),
        last_column=c.get("lastColumn",""))

_g('AVE', {'product': 'товар', 'pharmacy': 'Аптека', 'count': 'Продажи', 'amount': 'Сумма', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма'})
_g('AVESTOCK', {'product': 'Наименование товара', 'pharmacy': 'Наименование аптеки', 'count': '', 'amount': '', 'pharmacyNo': 'Код аптеки', 'city': '', 'remCount': 'Количество уп/Расход', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Количество уп/Расход'})
_g('RADUGAKARISIK', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('URAZMANOV', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('A5', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': '', 'amount': 'ПродажиД Кол-во упак с учетом разбивок', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'ПродажиД Кол-во упак с учетом разбивок'})
_g('RIGLA', {'product': 'Наименование', 'pharmacy': 'Сайт', 'count': 'Продажи, уп', 'amount': 'Продажи, закуп', 'pharmacyNo': 'Код АП', 'city': '', 'remCount': '', 'remAmount': '', 'lastColumn': 'Продажи, закуп'})
_g('RIIGLA', {'product': 'Наименование', 'pharmacy': 'Сайт', 'count': 'Продажи, уп', 'amount': 'Продажи, закуп', 'pharmacyNo': 'Код АП', 'city': '', 'remCount': '', 'remAmount': '', 'lastColumn': 'Продажи, закуп'})
_g('UNIVERSTITETSKIE', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('PLANETZDOROVIYA', {'product': 'Наименование товара', 'pharmacy': '', 'count': 'Продажи (кол-во)', 'amount': 'Продажи (сумма прих)', 'pharmacyNo': '', 'city': 'Регион', 'remCount': 'Остатки (кол-во)', 'remAmount': 'Остатки (сумма прих)', 'subgroup': '', 'lastColumn': 'Остатки (сумма прих)'})
_g('PLANETZDOROVIYASIMPLEVERTICAL', {'product': 'Наименование товара', 'pharmacy': '', 'count': 'Продажи (кол-во)', 'amount': '', 'pharmacyNo': '', 'city': 'Регион', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продажи (кол-во)'})
_g('PLANETZDOROVIYAPURCHASE', {'product': 'Товар', 'pharmacy': '', 'count': 'Кол-во', 'amount': 'Сумма с НДС', 'pharmacyNo': '', 'city': 'Регион', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма с НДС'})
_g('PLANETZDOROVIYANEW', {'product': 'Наименование товара', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование товара'})
_g('PLANETZDOROVIYAOLD', {'product': 'Продажи (кол-во)', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продажи (кол-во)'})
_g('EDELVESNEW', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('EDELVES', {'product': 'Товар', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Товар'})
_g('FARMLEND', {'product': 'Регионы', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Уфа'})
_g('FIALKA', {'product': 'Названия строк', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Названия строк'})
_g('KAZANSKY_APTEKI_', {'product': 'Препарат', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Препарат'})
_g('MELODIYA_ZDOROVIE_KRASNODAR_', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('NEVIS', {'product': 'Аптека, Адрес', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Аптека, Адрес'})
_g('NOVAYAAPTEKAKALININGRAD', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('PHARMAKOR', {'product': 'Группа по наименованию', 'pharmacy': 'Аптека', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Группа по наименованию'})
_g('RADUGA', {'product': 'Торговая точка', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Торговая точка'})
_g('RIFARM', {'product': 'Краткий текст материала', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('RIFARMNEW', {'product': 'Наименование2', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование2'})
_g('SAKURA', {'product': 'Товар', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Товар'})
_g('SAMSONPHARMA', {'product': 'Узел', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Название товара'})
_g('UNIVERSITESTSKYAPTEKI', {'product': 'Наименование товара', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование товара'})
_g('VITASAMARA', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('VITASAMARASTOCK', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('VITASAMARANEW', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('VITASAMARAPRODUCTHORIZONTAL', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('VITATOMSK', {'product': 'Товар/Наименование', 'pharmacy': 'Склад/Название', 'count': 'Продажи по чекам/Кол-во(шт)', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('ZDOROVRU', {'product': 'Название', 'pharmacy': 'Склад', 'count': 'Кол-во', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('MELODIYAZDOROVIYA', {'product': 'Адрес', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Адрес'})
_g('ZHIVIKA', {'product': 'Товар', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Названия строк'})
_g('ZHIVIKASTOCK', {'product': 'Названия строк', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Названия строк'})
_g('MELODIYAZDOROVYNOVOSIBIRSK', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('PERVAYAPOMOSHBARNAUL', {'product': 'Наименование', 'pharmacy': 'Аптечный пункт', 'count': 'Количество', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('PERVAYAPOMOSHBARNAULSTOCK', {'product': 'Продукт', 'pharmacy': 'Аптека', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остаток'})
_g('DOCTORSTOLETOV', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('MOSAPTEKA', {'product': 'Название товара', 'pharmacy': 'Отделы', 'count': 'Кол-во товара', 'amount': 'Сумма закупки с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('PANAZEYA', {'product': 'Наименование', 'pharmacy': '', 'count': 'Расход за период', 'amount': 'Расход за период', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('PERVAYAAPTEKAARHANGELSK', {'product': 'Подразделение', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Подразделение'})
_g('SOSIALNAYAAPTEKA', {'product': 'продукт рус.', 'pharmacy': 'адрес в базе', 'count': 'продажи уп.', 'amount': '', 'pharmacyNo': '', 'city': 'город', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('VESTA', {'product': 'продукт рус.', 'pharmacy': 'адрес в базе', 'count': 'продажи уп.', 'amount': '', 'pharmacyNo': '', 'city': 'город', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('APTEKIKUBANI', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('APTEKA245', {'product': 'Препарат', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Препарат'})
_g('APTEKA245STOCK', {'product': 'Товар', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Товар'})
_g('PILULI', {'product': 'Товар', 'pharmacy': 'Склад', 'count': 'Кол-во', 'amount': 'Себестоимость', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Себестоимость'})
_g('OTHERS', {'product': 'Product', 'pharmacy': 'PharmacyAddress', 'count': 'Count', 'amount': 'Amount', 'pharmacyNo': 'AptekaNo', 'city': 'City', 'remCount': '', 'remAmount': '', 'subgroup': 'SubGroup', 'lastColumn': 'City'})
_g('SHEKSNA', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('KLASSIKA', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('OAS', {'product': 'Коммерческое наименование Список', 'pharmacy': 'Адрес', 'count': 'Адрес', 'amount': '', 'pharmacyNo': '', 'city': 'Город', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Адрес'})
_g('DEJURNAYA', {'product': 'Название товара', 'pharmacy': 'Отдел', 'count': 'Кол-во', 'amount': 'Сумма закупки с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма закупки с НДС'})
_g('NIKA', {'product': 'Название товара', 'pharmacy': 'Отдел', 'count': 'Продажи', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продажи'})
_g('AVICENNA', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('DIALOG', {'product': 'Название', 'pharmacy': 'Склад', 'count': 'Кол-во прод', 'amount': 'Сумма прод', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Склад'})
_g('LISTIK', {'product': 'Название товара', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Название товара'})
_g('NOVAVITA', {'product': 'Названия строк', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Названия строк'})
_g('EVALAR', {'product': 'Наименование', 'pharmacy': 'Аптека', 'count': 'Кол-во', 'amount': 'Сумма поставки', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('SHEKSNANEW', {'product': 'Названия строк', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Названия строк'})
_g('FARMAKOPEYKA', {'product': 'Наименование', 'pharmacy': 'Аптека', 'count': 'Продажи', 'amount': 'Сумма в СИП', 'pharmacyNo': '', 'city': 'Продажи', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма в СИП'})
_g('SGA', {'product': 'Наименование ИРИС', 'pharmacy': 'Адрес', 'count': 'Количество в упак', 'amount': 'Сумма в ценах закупки от первичных дист с НДС', 'pharmacyNo': '', 'city': 'Город', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма в ценах закупки от первичных дист с НДС'})
_g('ROSA', {'product': 'Сумма оборота,', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма оборота,'})
_g('ROSANEW', {'product': '№', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': '№'})
_g('UNIFARMA', {'product': 'Товар', 'pharmacy': 'Склад', 'count': 'Количество', 'amount': 'Сумма закуп', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма закуп'})
_g('UNIFARMASTOCK', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток', 'remAmount': 'Сумма закуп с НДС Конечный остаток', 'subgroup': '', 'lastColumn': 'Сумма закуп с НДС Конечный остаток'})
_g('ZDOROVOE', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('KZTSETNAYA', {'product': 'Товар', 'pharmacy': 'Названия строк', 'count': 'Товар', 'amount': '', 'pharmacyNo': '', 'city': 'Город', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Товар'})
_g('KZFARMAKOM', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': 'Продажи (шт', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продажи (шт'})
_g('NEOPHARM', {'product': 'Номенклатура', 'pharmacy': 'Подразделение', 'count': 'Количество', 'amount': 'Сумма закупки', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма закупки'})
_g('NEOPHARMSTOCK', {'product': 'Номенклатура', 'pharmacy': 'Подразделение', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Количество', 'remAmount': 'Сумма закупки', 'subgroup': '', 'lastColumn': 'Сумма закупки'})
_g('SOLNYSHKO', {'product': 'Название товара', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Название товара'})
_g('VEKFARMA', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': 'Кол-во', 'amount': 'Сумма закупки с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма закупки с НДС'})
_g('VEKJIVI', {'product': 'Наименование', 'pharmacy': 'Аптека', 'count': 'Продажи кол-во упак.', 'amount': 'Продажи в Розн с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продажи в Розн с НДС'})
_g('FARMPREPARATI', {'product': 'Тип документа', 'pharmacy': 'Тип документа', 'count': 'Тип документа', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Тип документа'})
_g('APTEKAFORTE', {'product': 'Наименование, SKU', 'pharmacy': 'Наименование и адрес аптечной организации', 'count': 'Количество', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование и адрес аптечной организации'})
_g('TSELITEL', {'product': 'Название товара', 'pharmacy': 'Отдел', 'count': 'Количество', 'amount': 'Сумма по закупке с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Количество'})
_g('APTEKARSKIJDVOR', {'product': 'Чеки, расх.', 'pharmacy': '', 'count': 'Чеки, расх.', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Чеки, расх.'})
_g('LAKIFARM', {'product': 'Наименование', 'pharmacy': '', 'count': 'Наименование', 'amount': 'Наименование', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('DM', {'product': 'НАИМЕНОВАНИЕ ТОВАРА', 'pharmacy': 'АПТЕКА', 'count': 'ПРОДАЖИ уп.', 'amount': 'ПРОДАЖИ СУММА ЗЦ руб, с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'ПРОДАЖИ СУММА ЗЦ руб, с НДС'})
_g('VITAPLUS', {'product': 'Товар', 'pharmacy': '', 'count': 'Количество', 'amount': 'Сумма пост.(с НДС)', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Сумма пост.(с НДС)'})
_g('DOBRAYAAPTEKA', {'product': 'Товар', 'pharmacy': 'Фактический адрес', 'count': 'Количество продано, уп.', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Количество продано, уп.'})
_g('APTEKANAKRASNOM', {'product': 'Название товара', 'pharmacy': 'Отдел', 'count': 'Кол-во', 'amount': 'Цена закупки с НДС', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Цена закупки с НДС'})
_g('BELAYAAPTEKA', {'product': 'продано', 'pharmacy': '', 'count': 'продано', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'продано'})
_g('BELAYAAPTEKASTOCK', {'product': 'Конечный остаток', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Конечный остаток', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Конечный остаток'})
_g('APTEKAGORODA', {'product': 'Наименование', 'pharmacy': '', 'count': 'Наименование', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('FARMATON', {'product': 'Фирма / Товар', 'pharmacy': '', 'count': 'Расход', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Расход'})
_g('VITAMED', {'product': 'Наименование', 'pharmacy': 'Аптека', 'count': 'Кол-во по расходу', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Кол-во по расходу'})
_g('APTEKA313', {'product': 'Наименование', 'pharmacy': 'Подразделение', 'count': 'Продано', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продано'})
_g('APTEKA313', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('UKMEDICINEDELAVAS', {'product': 'Название', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Название'})
_g('UKROST', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('UKMEDSERVISHORIZONTAL', {'product': 'Место хранения.Владелец', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('NAS', {'product': 'наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'наименование'})
_g('GARMONIYAZDOROVIYASTOCK', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остаток'})
_g('VALEO', {'product': 'Отдел / Товар', 'pharmacy': '', 'count': 'Отдел / Товар', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Отдел / Товар'})
_g('OVITA', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('MONASTRIEV', {'product': 'Продукт', 'pharmacy': 'Аптека', 'count': 'Продажи', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остатки на конец периода', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остатки на конец периода'})
_g('MONASTRIEVSIMPLE', {'product': 'Продукт', 'pharmacy': 'Аптека', 'count': 'Продажи', 'amount': 'Цена ОПТ ср. взвеш.', 'pharmacyNo': '', 'city': '', 'remCount': 'Остатки на конец периода', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остатки на конец периода'})
_g('SOSVEZDIE', {'product': 'Промотовар', 'pharmacy': 'Аптека(адрес)', 'count': 'Кол-во реализовано, уп', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Кол-во реализовано, уп'})
_g('PROAPTEKA', {'product': 'Наименование товара', 'pharmacy': 'Адрес АУ', 'count': 'Продажи. Кол-во', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Продажи. Кол-во'})
_g('ZDOROVIYGOROD', {'product': 'Полное наименование', 'pharmacy': 'Аптека', 'count': 'Продано', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('APREL', {'product': 'Наименование', 'pharmacy': 'Аптека', 'count': 'Продано', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': ''})
_g('APRELSTOCK', {'product': 'Наименование товара', 'pharmacy': 'Наименование аптеки', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток аптека (кол-во)', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остаток аптека (кол-во)'})
_g('MAKSAVITSTOCK', {'product': 'Номенклатура', 'pharmacy': 'Подразделение компании', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Количество', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Количество'})
_g('APTECHNJMIR', {'product': 'Product', 'pharmacy': 'PharmacyAddress', 'count': 'Count', 'amount': 'Amount', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Amount'})
_g('VOLGOFARM', {'product': 'Наименование', 'pharmacy': 'Фактический адрес аптеки', 'count': 'Проданные упаковки', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Проданные упаковки'})
_g('FARMACEVTPLYUS', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': 'Продажи упаковки', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Товар'})
_g('FARMACEVTPLYUSSTOCK', {'product': 'Наименование товара', 'pharmacy': 'Адрес', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток', 'remAmount': 'Цена пост с НДС', 'subgroup': '', 'lastColumn': 'Цена пост с НДС'})
_g('BLPLANETZDOROVYIA', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': 'Май продажи', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остаток'})
_g('BLDOCTORVREMYA', {'product': 'Товар', 'pharmacy': 'Аптека', 'count': 'Май продажи', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': 'Остаток', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Остаток'})
_g('EKONOM', {'product': 'Наименование ИнфоАптека', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование ИнфоАптека'})
_g('KZASNA', {'product': 'Наименование Товара', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование Товара'})
_g('KZSALAMAT', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('AZAVROMED', {'product': 'Sales', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Sales'})
_g('AZBUTA', {'product': 'Name', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Name'})
_g('SKANDINAVIYAHORIZONTALSIMPLE', {'product': 'Наименование', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Наименование'})
_g('AMVITAPARK', {'product': 'Адрес', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Адрес'})
_g('AMGEDEONRIHTER', {'product': 'Аналитика товара', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Аналитика товара'})
_g('KZZERDEVERTICAL', {'product': 'Номенклатура', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура'})
_g('KZVITAVERTICAL', {'product': 'Номенклатура, Базовая единица измерения', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Номенклатура, Базовая единица измерения'})
_g('KZSADYKHANVERTICAL', {'product': 'Склад', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Склад'})
_g('KGNEMAN', {'product': 'Товары', 'pharmacy': '', 'count': '', 'amount': '', 'pharmacyNo': '', 'city': '', 'remCount': '', 'remAmount': '', 'subgroup': '', 'lastColumn': 'Товары'})


# ---- NESTED (iç içe) ----
_PH = ["Аптека", "Склад", "фарм"]
_PR = ["Солгар", "СОЛГАР", "Solgar"]
NESTED = {
    "OLFA": NestedConfig("OLFA", product="Номенклатура", last_column="Номенклатура"),
    "MEDSERVIS": NestedConfig("MEDSERVIS", product="Номенклатура", last_column="Номенклатура"),
    "MARKET_UNIVERSAL": NestedConfig("MARKET_UNIVERSAL", product="Номенклатура", last_column="Номенклатура"),
    "ANNUSHKA": NestedConfig("ANNUSHKA", product="Номенклатура", last_column="Номенклатура",
                             pharmacy_markers=["Аптека"], product_markers=[], product_starts_with="("),
    "GORMANALNIH": NestedConfig("GORMANALNIH", product="Номенклатура", last_column="Номенклатура",
                                pharmacy_markers=["Аптека"], product_markers=[], product_starts_with="("),
    "ASTARTA": NestedConfig("ASTARTA", product="Товар", count="Количество расход", amount="Сумма зак расход", last_column="Сумма зак расход"),
    "LEDA": NestedConfig("LEDA", product="Номенклатура", count="Продажа", last_column="Продажа"),
    "FARMSFERA": NestedConfig("FARMSFERA", product="Филиал", count="Количество расход", last_column="Количество расход"),
    "LEKFARM": NestedConfig("LEKFARM", product="Номенклатура", count="Продажа", last_column="Продажа"),
}

# ---- HORIZONTAL (pivot) ----
HORIZONTAL = {
    "SIRIUS95": HorizontalConfig("SIRIUS95", product_keyword="Товар", start_column=7),
    "VITA_SAMARA": HorizontalConfig("VITA_SAMARA", product_keyword="Наименование"),
    "MEDSERVIS_H": HorizontalConfig("MEDSERVIS_H", product_keyword="Место хранения"),
    "SKANDINAVIYA": HorizontalConfig("SKANDINAVIYA", product_keyword="Товар"),
}

# ---- SPECIAL (extract rules) ----
def _ave():
    c = GenericConfig("AVE", product="товар", pharmacy="Аптека", count="Продажи", amount="Сумма", last_column="Сумма")
    c.extract_rules = [
        ExtractRule2("PHARMACY","SUBGROUP",ExtractMode2.CONTAINS_FIXED,"36,6",fixed_result="36.6",remove=False),
        ExtractRule2("PHARMACY","SUBGROUP",ExtractMode2.BEFORE_MARKER,",",fallback="$MAINGROUP"),
        ExtractRule2("PHARMACY","APTEKNO",ExtractMode2.AFTER_MARKER,". Аптека",offset=2),
    ]
    return c

def _nevis():
    c = GenericConfig("NEVIS", product="Аптека, Адрес", pharmacy="Аптека, Адрес", last_column="Аптека, Адрес")
    c.extract_rules = [
        ExtractRule2("SALESREADER","APTEKNO",ExtractMode2.BEFORE_MARKER,",",remove=False),
        ExtractRule2("SALESREADER","PHARMACY",ExtractMode2.AFTER_MARKER,",",offset=1,remove=False),
    ]
    return c

SPECIAL = {"AVE": _ave(), "NEVIS": _nevis()}


def get_config(chain_or_file):
    """Zincir/dosya adindan (config, motor_tipi) dondur."""
    if not chain_or_file:
        return None, None
    up = chain_or_file.upper()
    # Sirasiyla: Simple (dogrulanmis) > Special > Nested > Horizontal > Generic
    for key, cfg in SIMPLE_CONFIGS.items():
        if key in up: return cfg, "simple"
    for key, cfg in SPECIAL.items():
        if key in up: return cfg, "special"
    for key, cfg in NESTED.items():
        if key in up: return cfg, "nested"
    for key, cfg in HORIZONTAL.items():
        if key in up: return cfg, "horizontal"
    for key, cfg in GENERIC.items():
        if key in up: return cfg, "generic"
    return None, None


def all_chains():
    """Tum zincir adlari (dropdown icin)."""
    s = set()
    s.update(SPECIAL.keys()); s.update(NESTED.keys())
    s.update(HORIZONTAL.keys()); s.update(GENERIC.keys())
    s.update(SIMPLE_CONFIGS.keys())
    return sorted(s)


def parse_chain(sheet, chain_or_file, main_group, v_limit, h_limit):
    """Zinciri dogru motorla parse et. list[dict] doner (bulunamzsa None)."""
    cfg, typ = get_config(chain_or_file)
    if cfg is None:
        return None
    if typ == "simple":
        return PharmacyParser().parse(sheet, cfg, main_group, v_limit, h_limit)
    if typ in ("generic", "special"):
        return GenericParser().parse(sheet, cfg, main_group, v_limit, h_limit)
    if typ == "nested":
        return NestedParser().parse(sheet, cfg, main_group, v_limit, h_limit)
    if typ == "horizontal":
        return HorizontalParser().parse(sheet, cfg, main_group, v_limit, h_limit)
    return None
