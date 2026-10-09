from sales.models import ChainDefinition

# AVE eczane zinciri - Excel kolonlarina gore column_map
# Excel: Код товара | Наименование товара | Код аптеки | Наименование аптеки |
#        Количество уп/Расход | Сумма закуп без НДС/Расход
obj, created = ChainDefinition.objects.get_or_create(
    name="AVE",
    source_type=ChainDefinition.SourceType.PHARMACY,
    defaults={
        "is_active": True,
        "orientation": ChainDefinition.Orientation.VERTICAL,
        "header_search_limit": 30,
        "column_map": {
            "product": "Наименование товара",
            "pharmacy": "Наименование аптеки",
            "count": "Количество уп/Расход",
            "amount": "Сумма закуп без НДС/Расход",
        },
    },
)
print(f"AVE: {'olusturuldu' if created else 'zaten var'}")
print("column_map:", obj.column_map)
print("\nTum eczane zincirleri:")
for d in ChainDefinition.objects.filter(source_type=ChainDefinition.SourceType.PHARMACY):
    print(f"  {d.name}: {d.column_map}")
