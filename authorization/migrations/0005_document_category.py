"""
authorization — FAQ dokuman klasorleri (DocumentCategory) + Document'a klasor
(category), orijinal dosya adi (original_name). content_type artik her tur
dosya (default octet-stream), max_length 120.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("authorization", "0004_document"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="Название папки")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
            ],
            options={
                "verbose_name": "Папка документов (FAQ)",
                "verbose_name_plural": "Папки документов (FAQ)",
                "db_table": "authorization_document_category",
                "ordering": ["order", "name"],
            },
        ),
        migrations.AddField(
            model_name="document",
            name="category",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="documents",
                to="authorization.documentcategory",
                verbose_name="Папка",
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="original_name",
            field=models.CharField(blank=True, editable=False, max_length=255, verbose_name="Имя файла"),
        ),
        migrations.AlterField(
            model_name="document",
            name="content",
            field=models.BinaryField(editable=False, verbose_name="Содержимое файла"),
        ),
        migrations.AlterField(
            model_name="document",
            name="content_type",
            field=models.CharField(default="application/octet-stream", editable=False, max_length=120, verbose_name="MIME"),
        ),
    ]
