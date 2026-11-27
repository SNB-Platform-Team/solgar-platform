"""
authorization — add the Territory Manager Dashboard (TM_DASHBOARD) Screen.

Teritori yoneticisi dashboard'u (Регион/Медреп/Активность/Категория 4 tablo)
admin panelde AccessLevel'in "Accessible screens" listesinde secilebilsin diye
bir Screen kaydi olarak eklenir. code=TM_DASHBOARD. Backend gate'i
HasScreen("TM_DASHBOARD"), frontend menu/route de ayni ekran koduyla gate'lenir.

Ek olarak: 'territory_manager' adli bir AccessLevel VARSA bu ekrani ona otomatik
baglar (boylece deploy sonrasi elle atama gerekmez; yoksa sessizce atlar —
ekran yine de admin'den istenen level'a atanabilir).

Idempotent: tekrar calisirsa duplicate olusturmaz / ad gunceller.
"""

from django.db import migrations


def seed_tm_dashboard(apps, schema_editor):
    Screen = apps.get_model("authorization", "Screen")
    AccessLevel = apps.get_model("authorization", "AccessLevel")

    screen, _ = Screen.objects.update_or_create(
        code="TM_DASHBOARD",
        defaults={
            "name": "Дашборд территориального менеджера",
            "description": "4 таблицы: регион/медреп/активность/категория",
            "order": 60,
            "is_active": True,
        },
    )

    # 'territory_manager' level'i varsa ekrani ona bagla (buyuk/kucuk duyarsiz).
    for lvl in AccessLevel.objects.all():
        if (lvl.name or "").strip().lower() == "territory_manager":
            lvl.screens.add(screen)


def unseed_tm_dashboard(apps, schema_editor):
    Screen = apps.get_model("authorization", "Screen")
    Screen.objects.filter(code="TM_DASHBOARD").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authorization", "0005_document_category"),
    ]

    operations = [
        migrations.RunPython(seed_tm_dashboard, unseed_tm_dashboard),
    ]
