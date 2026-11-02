"""
sales — PharmacyEquipment + PharmacyEquipmentPhoto (platformun kendi ekipman
kayitlari). Eski solgar_cor.corner_info salt-okunur kalir; yeni kayitlar bu
tablolara yazilir. Fotograflar Azure Blob'da, burada sadece blob adi tutulur.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0011_geocodesettings"),
    ]

    operations = [
        migrations.CreateModel(
            name="PharmacyEquipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("pharmacy_id", models.IntegerField(db_index=True, verbose_name="Pharmacy ID (legacy)")),
                ("brand", models.CharField(default="SOLGAR", max_length=20, verbose_name="Brand")),
                ("promo", models.CharField(blank=True, max_length=120, verbose_name="Промо")),
                ("subtype", models.CharField(blank=True, max_length=200, verbose_name="Подтип")),
                ("size", models.CharField(blank=True, max_length=120, verbose_name="Размер")),
                ("status", models.PositiveSmallIntegerField(default=1, verbose_name="Статус")),
                ("created_by", models.CharField(blank=True, max_length=255, verbose_name="Создал")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
            ],
            options={
                "verbose_name": "Оборудование аптеки",
                "verbose_name_plural": "Оборудование аптек",
                "db_table": "intern_pharmacy_equipment",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PharmacyEquipmentPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("blob_name", models.CharField(max_length=300, verbose_name="Blob name")),
                ("content_type", models.CharField(default="image/jpeg", max_length=120, verbose_name="MIME")),
                ("original_name", models.CharField(blank=True, max_length=255, verbose_name="Имя файла")),
                ("size", models.PositiveIntegerField(default=0, verbose_name="Размер (байт)")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("equipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="sales.pharmacyequipment", verbose_name="Оборудование")),
            ],
            options={
                "verbose_name": "Фото оборудования",
                "verbose_name_plural": "Фото оборудования",
                "db_table": "intern_pharmacy_equipment_photo",
                "ordering": ["id"],
            },
        ),
    ]
