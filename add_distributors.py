"""
Toplu distributor ChainDefinition oluşturma - Java Storages.java'dan çıkarılan başlıklar.
Django shell'de çalıştır: python manage.py shell < add_distributors.py
Ya da içeriğini shell'e yapıştır.
"""
from sales.models import ChainDefinition

# Java parser başlıklarından çıkarılan column_map'ler.
# name: dosya adıyla eşleşmeli (dosya adı kontrolü için).
DISTRIBUTORS = [
    {
        "name": "ПРОТЕК",  # Протек продажи... dosyası
        "column_map": {
            "product": "наименование",
            "count": "отгружено",
            "city": "регион",
            "client": "клиент",
        },
    },
    {
        "name": "РИГЛА",  # Ригла_Солгар остатки... dosyası
        "column_map": {
            "product": "Наименование препарата",
            "count": "Количество",
            "city": "Получатель",
            "client": "Поставщик",
        },
    },
    {
        "name": "ГРАНД КАПИТАЛ",  # Гранд Капитал продажи... dosyası
        "column_map": {
            "product": "_Название Товара",
            "count": "Кол-во",
            "city": "Регион",
            "client": "Имя Контрагента Краткое",
        },
    },
    {
        "name": "ЭМИТИ",  # Эмити_Продажи / ЭМИТИ_STOCK dosyası
        "column_map": {
            "product": "Товар",
            "count": "Продажи, шт.",
            "city": "Отдел",
        },
    },
]

for d in DISTRIBUTORS:
    obj, created = ChainDefinition.objects.get_or_create(
        name=d["name"],
        source_type=ChainDefinition.SourceType.DISTRIBUTOR,
        defaults={
            "is_active": True,
            "orientation": ChainDefinition.Orientation.VERTICAL,
            "header_search_limit": 30,
            "column_map": d["column_map"],
        },
    )
    status = "oluşturuldu" if created else "zaten var"
    print(f"{d['name']}: {status}")

print("\nTüm distributor tanımları:")
for c in ChainDefinition.objects.filter(source_type=ChainDefinition.SourceType.DISTRIBUTOR):
    print(f"  {c.name}: {c.column_map}")
