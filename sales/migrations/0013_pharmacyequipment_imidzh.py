"""
sales — PharmacyEquipment'e imidzh (Имидж / POS gorseli adi) alani eklenir.

Оборудование demo: promo 'must have имидж' ise (solgar_cor.presence_image=1)
kullanici brand'ine gore (POS_SL / POS_NB) bir urun imidji secer; secilen
imidj ADI bu kolonda tutulur. Must-have degilse bos.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0012_pharmacy_equipment"),
    ]

    operations = [
        migrations.AddField(
            model_name="pharmacyequipment",
            name="imidzh",
            field=models.CharField(blank=True, max_length=255, verbose_name="Имидж"),
        ),
    ]
