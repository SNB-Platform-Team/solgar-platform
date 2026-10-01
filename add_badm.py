from sales.models import ChainDefinition

ChainDefinition.objects.get_or_create(
    name="БАДМ",
    source_type=ChainDefinition.SourceType.DISTRIBUTOR,
    defaults={
        "is_active": True,
        "orientation": ChainDefinition.Orientation.VERTICAL,
        "header_search_limit": 30,
        "column_map": {
            "product": "Товар",
            "count": "Кількість реальна",
            "city": "Склад",
        },
    },
)
print("БАДМ eklendi")
print("Distributor:", list(ChainDefinition.objects.filter(source_type=ChainDefinition.SourceType.DISTRIBUTOR).values_list("name", flat=True)))
