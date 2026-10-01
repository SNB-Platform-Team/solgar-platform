from sales.models import ChainDefinition

# Latin VITALAINSAMARA sil
ChainDefinition.objects.filter(name="VITALAINSAMARA").delete()

# Kiril ВИТАЛАЙНСАМАРА ekle (dropdown/prm_storages ile eslesir)
ChainDefinition.objects.get_or_create(
    name="ВИТАЛАЙНСАМАРА",
    source_type=ChainDefinition.SourceType.DISTRIBUTOR,
    defaults={
        "is_active": True,
        "orientation": ChainDefinition.Orientation.VERTICAL,
        "header_search_limit": 30,
        "column_map": {"product": "Наименование"},
    },
)
print("VITALAINSAMARA (Latin) -> ВИТАЛАЙНСАМАРА (Kiril)")
print("Distributor:", list(ChainDefinition.objects.filter(source_type=ChainDefinition.SourceType.DISTRIBUTOR).values_list("name", flat=True)))
