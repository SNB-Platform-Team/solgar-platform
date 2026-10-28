"""
authorization — add the Главная (home/dashboard) Screen.

Главная ekrani admin panelde AccessLevel'in "Accessible screens" listesinde
secilebilsin diye bir Screen kaydi olarak eklenir. code=HOME, order=0 (en ust).
Idempotent: tekrar calisirsa ad/order gunceller, duplicate olusturmaz.
"""

from django.db import migrations


def seed_home(apps, schema_editor):
    Screen = apps.get_model("authorization", "Screen")
    Screen.objects.update_or_create(
        code="HOME",
        defaults={"name": "Главная", "order": 0, "is_active": True},
    )


def unseed_home(apps, schema_editor):
    Screen = apps.get_model("authorization", "Screen")
    Screen.objects.filter(code="HOME").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authorization", "0002_seed_screens"),
    ]

    operations = [
        migrations.RunPython(seed_home, unseed_home),
    ]
