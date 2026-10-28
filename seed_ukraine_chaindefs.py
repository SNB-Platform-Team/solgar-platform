"""
Ukrayna zincirleri icin ChainDefinition seed (sales-upload parser tanimlari).

Sales-upload (Загрузка продаж) dropdown'u ve parser'i ChainDefinition
tablosundan okur. Ukrayna zincirlerinin tanimi yoktu -> "Сеть не найдена".
Bu script, 16 ornek dosyadan column_map'i dogrulanmis 14 zinciri ekler.
MARKET_UNIVERSAL ve MED-SERVICE haric (ozel format, standart parser'a uymuyor).

name degerleri solgar_prm.prm_ukraine_chains'teki yazimla birebir ayni
(dropdown oradan degil ChainDefinition'dan gelir, ama tutarli olsun diye
ayni yazim kullanildi).

Calistir (Azure SSH veya lokal):
    python manage.py shell
    exec(open("seed_ukraine_chaindefs.py", encoding="utf-8").read())
"""

from sales.models import ChainDefinition

PHARMACY = ChainDefinition.SourceType.PHARMACY

# name -> column_map  (hepsi dogrulandi: ChainParser bu basliklari buluyor
# ve urun satirlari okunuyor). count = satis adedi (расход/продажи/
# реализація), amount = satis tutari.
UA_CHAINS = {
    "SIRIUS-95": {"product": "Препарат", "pharmacy": "Аптека", "city": "Область",
                  "count": "Количество единиц", "amount": "Закупочная сумма (без НДС)"},
    "ZDOROVA RODYNA": {"product": "Товар", "pharmacy": "Филиал", "city": "Область",
                       "count": "Расход-чеки", "amount": "Расход чеки сумма с НДС (зак.)"},
    "ZDRAVITSA": {"product": "Товар", "pharmacy": "Филиал",
                  "count": "Количество расход", "amount": "Сумма зак расход"},
    "ANCOR-FARM": {"product": "Номенклатура", "count": "Расход"},
    "APTEKA_NC": {"product": "Товар", "pharmacy": "Филиал",
                  "count": "Количество расход", "amount": "Сумма розн расход"},
    "ASTARTA": {"product": "Товар", "pharmacy": "Филиал",
                "count": "Количество расход", "amount": "Сумма зак расход"},
    "DOBROBUT": {"product": "Товар", "pharmacy": "Аптека",
                 "count": "Кількість", "amount": "Сума зак"},
    "FARMASTOR": {"product": "Товар", "pharmacy": "Филиал",
                  "count": "Кол-во продаж", "amount": "Сумма продаж в зак бНДС"},
    "FOZZI-FARM": {"product": "Найменування", "pharmacy": "Аптека",
                   "count": "Кількість", "amount": "Сума без ПДВ"},
    "GAEVSKOGO": {"product": "Товар", "pharmacy": "Филиал",
                  "count": "Количество Расход", "amount": "СуммаЗак Расход"},
    "GAMMA": {"product": "Номенклатура", "pharmacy": "СкладТТ", "city": "Область",
              "count": "ПродажиКоличество", "amount": "ПродажиСумма"},
    "PODOROZHNIK": {"product": "Товар", "pharmacy": "Підрозділ",
                    "count": "Розх ксть уп", "amount": "Розх сума закуп"},
    "3І": {"product": "Назва", "pharmacy": "Аптека",
           "count": "Реалізація", "amount": "Реалізація"},
    "MAGNOLIYA": {"product": "Наименование", "pharmacy": "Аптека", "city": "Город",
                  "count": "Расход упак.", "amount": "Сумма расхода (приходн.)"},
}

created, updated = 0, 0
for name, cmap in UA_CHAINS.items():
    obj, was_created = ChainDefinition.objects.update_or_create(
        name=name,
        source_type=PHARMACY,
        defaults={
            "country": "Ukraine",
            "orientation": "VERTICAL",
            "column_map": cmap,
            "header_search_limit": 30,
            "is_active": True,
        },
    )
    if was_created:
        created += 1
        print("CREATED:", name)
    else:
        updated += 1
        print("UPDATED:", name)

print(f"\nToplam: {created} eklendi, {updated} guncellendi.")
print("Ukrayna PHARMACY tanimlari:",
      ChainDefinition.objects.filter(country="Ukraine", source_type=PHARMACY,
                                     is_active=True).count())
