"""
authorization — FAQ dokumanlari icin Document modeli.

PDF icerigi DB'de (BinaryField) saklanir; Azure App Service diski deploy'da
sifirlandigi icin dosya tabanli depolama kalici degil, DB kalici.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authorization", "0003_seed_home_screen"),
    ]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Название")),
                ("content", models.BinaryField(editable=False, verbose_name="PDF содержимое")),
                ("content_type", models.CharField(default="application/pdf", editable=False, max_length=100, verbose_name="MIME")),
                ("size", models.PositiveIntegerField(default=0, editable=False, verbose_name="Размер (байт)")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                ("uploaded_at", models.DateTimeField(auto_now=True, verbose_name="Загружено")),
            ],
            options={
                "verbose_name": "Документ (FAQ)",
                "verbose_name_plural": "Документы (FAQ)",
                "db_table": "authorization_document",
                "ordering": ["order", "title"],
            },
        ),
    ]
