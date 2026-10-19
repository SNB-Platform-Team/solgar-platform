"""
authorization — seed the Screen catalogue.

Creates one Screen row per platform page/module. Screen `code` values are
the stable identifiers used by:
  - the API permission check (HasScreen),
  - the React sidebar/route filter (me_api -> screens),
  - the @require_screen view decorator.

Idempotent: re-running updates names/order, never duplicates. Which
AccessLevel sees which Screen is NOT set here — that is managed by the
admin in Django admin (AccessLevel -> Chosen screens).
"""

from django.db import migrations


# (code, display name RU, menu order). Codes mirror the React sidebar URLs.
SCREENS = [
    ("SALES_UPLOAD", "Аптечной Сети Ввод Продаж&Сток", 10),
    ("CHAIN_REPORT", "Аптечной Сети Просмотр Продаж&Сток", 20),
    ("DIST_UPLOAD", "Дистрибьютор Ввод Продаж&Сток", 30),
    ("SALES_OBS", "Дистрибьютор Просмотр Продаж&Сток", 40),
    ("PHARMACY", "Аптек Управление Данными", 50),
    ("DOCTOR", "Врач Управление Данными", 60),
    ("PHARM_MGR", "Аптек Сводный Обзор", 70),
    ("DOCTOR_MGR", "Врач Сводный Обзор", 80),
    ("ONEC_STOCK", "1C — Склад", 90),
    ("ANALYTICS", "Аналитика (1C / Power BI)", 100),
    ("EMPLOYEES", "Сотрудники", 110),
    ("FAQ", "FAQ", 120),
]


def seed_screens(apps, schema_editor):
    """Create/update the Screen rows."""
    Screen = apps.get_model("authorization", "Screen")
    for code, name, order in SCREENS:
        Screen.objects.update_or_create(
            code=code,
            defaults={"name": name, "order": order, "is_active": True},
        )


def unseed_screens(apps, schema_editor):
    """Remove the seeded Screen rows (reverse migration)."""
    Screen = apps.get_model("authorization", "Screen")
    Screen.objects.filter(code__in=[c for c, _, _ in SCREENS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authorization", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_screens, unseed_screens),
    ]
