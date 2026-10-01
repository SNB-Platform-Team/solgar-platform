from sales.models import ChainDefinition

# PULSE Sales - Номенклатура/Регион доставки/Продано шт (New versiyon)
ChainDefinition.objects.get_or_create(
    name="ПУЛЬС",
    source_type=ChainDefinition.SourceType.DISTRIBUTOR,
    defaults={
        "is_active": True,
        "orientation": ChainDefinition.Orientation.VERTICAL,
        "header_search_limit": 30,
        "column_map": {
            "product": "Номенклатура",
            "city": "Регион доставки",
            "count": "Продано шт",
        },
    },
)

print("Distributor tanımları:")
for c in ChainDefinition.objects.filter(source_type=ChainDefinition.SourceType.DISTRIBUTOR):
    print(f"  {c.name}: {c.column_map}")
