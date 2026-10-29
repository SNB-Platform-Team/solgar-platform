"""
menu_access — solgar_org.menu_user_relation tabanli AccessLevel esleme mantigi.

Hem `sync_access_from_menu` management komutu hem de SSO callback
(accounts.views.azure_callback_view) buradan beslenir; boylece ikisi asla
ayrismaz. Tek kaynak: menu_user_relation'daki 9 yetki kolonu -> platform
Screen kodlari. Her benzersiz kombinasyon ("imza") bir AccessLevel'e karsilik
gelir; FAQ her seviyede bulunur (herkese acik).

Kullanim (SSO, ilk giriste):
    from authorization.menu_access import level_for_email
    lvl = level_for_email(user.email)   # None ise menu'de yok / eslesmedi
"""

from django.db import connections


# Platform Screen kodu -> menu_user_relation kolonu (Olga/DBA onayli esleme).
# FAQ her seviyede; ONEC_STOCK/ANALYTICS sadece admin (burada yok).
SCREEN_TO_MENU_COL = {
    "SALES_UPLOAD": "sales_entry",
    "CHAIN_REPORT": "sales_observation",
    "DIST_UPLOAD": "distrubutor_sale_stock",
    "SALES_OBS": "distrubutor_sale_observation",
    "PHARMACY": "pharm_data_definition",
    "DOCTOR": "doctor_data_definition",
    "PHARM_MGR": "executive_pharmacy",
    "DOCTOR_MGR": "executive_doctor",
    "EMPLOYEES": "staff_definition",
}
# AccessLevel adinda kullanilan kisa etiketler (admin panelde gorunur).
SCREEN_SHORT = {
    "SALES_UPLOAD": "Ввод АС",
    "CHAIN_REPORT": "Просмотр АС",
    "DIST_UPLOAD": "Ввод Дистр",
    "SALES_OBS": "Просмотр Дистр",
    "PHARMACY": "Аптеки",
    "DOCTOR": "Врачи",
    "PHARM_MGR": "Аптеки Обзор",
    "DOCTOR_MGR": "Врачи Обзор",
    "EMPLOYEES": "Сотрудники",
}
ALWAYS_SCREEN = "FAQ"  # her AccessLevel'de bulunur (herkese acik)

# Sabit kolon sirasi (imza bit-string'i icin). SCREEN_TO_MENU_COL sirasi.
ORDER = list(SCREEN_TO_MENU_COL.keys())
MENU_COLS = [SCREEN_TO_MENU_COL[s] for s in ORDER]


def norm(s):
    """Isim/email normalize: trim + lower + tek bosluk."""
    return " ".join((s or "").strip().lower().split())


def _bit_on(b):
    """menu kolonu degeri 'acik' mi? (int 1, '1', True ...)."""
    if b is None:
        return False
    try:
        return int(b) == 1
    except (TypeError, ValueError):
        return str(b).strip() in ("1", "1.0", "true", "True")


def signature_from_bits(bits):
    """menu satirinin 9 yetki kolonundan '0/1' imza string'i uret.

    sync_access_from_menu komutuyla ayni mantik (int(b) == 1), yoksa SSO
    imzasi komutun urettigi imzayla eslesmez ve yanlis level atanir.
    """
    return "".join("1" if _bit_on(b) else "0" for b in bits)


def screens_for_signature(sig):
    """Imzadan acik ekran kodlari (eslenen 9 + her zaman FAQ)."""
    on = [ORDER[i] for i, c in enumerate(sig) if c == "1"]
    return on + [ALWAYS_SCREEN]


def label_for_signature(sig):
    """Imzadan AccessLevel adi (kisa etiketler, admin panelde gorunur)."""
    on = [ORDER[i] for i, c in enumerate(sig) if c == "1"]
    if on:
        return ", ".join(SCREEN_SHORT[s] for s in on)[:78]
    return "Нет доступа"


def signature_for_email(email, _cache={}):
    """
    email -> menu_user_relation imzasi (ya da None).

    Kopru: email -> solgar_org.employees.EMPLOYEE_NAME ->
    menu_user_relation.employee_name -> o satirin yetki kombinasyonu.
    refdb (Sber) uzerinden raw SQL. Bulunamazsa None.
    """
    e = norm(email)
    if not e or "@" not in e:
        return None

    # email -> employee_name
    name = None
    with connections["refdb"].cursor() as cur:
        cur.execute(
            "SELECT EMPLOYEE_NAME FROM solgar_org.employees "
            "WHERE LOWER(TRIM(EMPLOYEE_EMAIL)) = %s "
            "AND EMPLOYEE_NAME IS NOT NULL AND EMPLOYEE_NAME <> '' "
            "ORDER BY id LIMIT 1",
            [e],
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return None
    name = norm(row[0])

    # employee_name -> menu satiri (yetki kolonlari)
    with connections["refdb"].cursor() as cur:
        cur.execute(
            f"SELECT {', '.join(MENU_COLS)} "
            f"FROM solgar_org.menu_user_relation "
            f"WHERE LOWER(TRIM(employee_name)) = %s LIMIT 1",
            [name],
        )
        mrow = cur.fetchone()
    if mrow is None:
        return None
    return signature_from_bits(mrow)


def get_or_create_level_for_signature(sig):
    """
    Imzaya karsilik gelen AccessLevel'i dondur (yoksa olustur).

    Ekran setine TAM uyan mevcut bir level varsa onu kullanir (sync komutuyla
    ayni sonuc). Yoksa adi label_for_signature'dan, ekranlari imzadan olan yeni
    bir level yaratir. Screen kataloglari eksikse ilgili ekran atlanir.
    """
    from authorization.models import AccessLevel, Screen

    want_codes = set(screens_for_signature(sig))
    screens = {s.code: s for s in Screen.objects.filter(code__in=want_codes)}
    want = {screens[c] for c in want_codes if c in screens}

    # Ekran seti TAM ayni olan mevcut level'i ara.
    for lvl in AccessLevel.objects.prefetch_related("screens"):
        if set(lvl.screens.all()) == want:
            return lvl

    # Yoksa olustur. Ad cakismasini onlemek icin gerekirse imza eklenir.
    base = label_for_signature(sig)
    name = base
    if AccessLevel.objects.filter(name=name).exists():
        name = f"{base} [{sig}]"[:80]
    lvl = AccessLevel.objects.create(
        name=name, rank=1, description=f"auto: menu sig {sig}"
    )
    if want:
        lvl.screens.set(list(want))
    return lvl


def level_for_email(email):
    """
    email -> AccessLevel (ilk giriste SSO icin). Menu'de yoksa None.

    None donerse cagiran taraf kendi fallback'ini uygular (orn. rank=1).
    DB/baglanti hatasinda da None (giris engellenmez).
    """
    try:
        sig = signature_for_email(email)
    except Exception:
        return None
    if sig is None:
        return None
    try:
        return get_or_create_level_for_signature(sig)
    except Exception:
        return None
