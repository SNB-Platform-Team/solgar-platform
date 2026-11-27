from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_user_multi_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="allowed_districts",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Список district'ов (как в solgar_address_group.district, "
                    "напр. ['South','Ural']). Для territory_manager: его "
                    "территория. Работает вместе с allowed_regions."
                ),
                verbose_name="Разрешённые округа (district, список)",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="allowed_regions",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Список region'ов (как в solgar_address_group.region, "
                    "напр. ['Rostov','Krasnodar']). Для territory_manager: его "
                    "территория. Работает вместе с allowed_districts."
                ),
                verbose_name="Разрешённые регионы (region, список)",
            ),
        ),
    ]
