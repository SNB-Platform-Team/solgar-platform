from sales.models import ChainDefinition

# VITALAINSAMARA - ozel parser kullanir (column_map onemli degil ama product yaz)
ChainDefinition.objects.get_or_create(
    name="VITALAINSAMARA",
    source_type=ChainDefinition.SourceType.DISTRIBUTOR,
    defaults={
        "is_active": True,
        "orientation": ChainDefinition.Orientation.VERTICAL,
        "header_search_limit": 30,
        "column_map": {"product": "Наименование"},  # ozel parser son kolonu count alir
    },
)
print("VITALAINSAMARA eklendi")
print("Distributor:", list(ChainDefinition.objects.filter(source_type=ChainDefinition.SourceType.DISTRIBUTOR).values_list("name", flat=True)))
