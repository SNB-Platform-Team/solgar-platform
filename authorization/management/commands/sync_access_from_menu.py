"""
sync_access_from_menu — solgar_org.menu_user_relation'dan AccessLevel'leri ve
MEVCUT platform kullanicilarinin yetkilerini senkronlar.

Tek seferlik aktarim (sonra admin panelden serbestce duzenlenir). Calistirma:
    python manage.py sync_access_from_menu --dry-run   # hicbir sey yazmaz, rapor
    python manage.py sync_access_from_menu             # gercek senkron

Mantik:
  - menu_user_relation'daki 9 yetki kolonu -> platform Screen kodlari (esleme
    asagida _SCREEN_TO_MENU_COL). 1 = erisim var.
  - Her benzersiz kombinasyon icin bir AccessLevel olusturulur (varsa guncellenir).
    FAQ her seviyede dahildir (herkese acik). ONEC_STOCK / ANALYTICS senkronda
    ATANMAZ (sadece admin/superuser gorur).
  - Kullanici eslesmesi: User.email -> solgar_org.employees.EMPLOYEE_EMAIL ->
    EMPLOYEE_NAME -> menu_user_relation.employee_name -> o satirin kombinasyonu.
    Sadece platformda ZATEN VAR OLAN User'lara atanir.
  - Superuser'lara dokunulmaz (zaten tum ekranlari gorur).
"""

from django.core.management.base import BaseCommand
from django.db import connections, transaction


# Platform Screen kodu -> menu_user_relation kolonu (Olga/DBA onayli esleme).
# FAQ her seviyede; ONEC_STOCK/ANALYTICS sadece admin (burada yok).
_SCREEN_TO_MENU_COL = {
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
_SCREEN_SHORT = {
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
_ALWAYS_SCREEN = "FAQ"  # her AccessLevel'de bulunur (herkese acik)

# Sabit kolon sirasi (kombinasyon imzasi icin). _SCREEN_TO_MENU_COL sirasi.
_ORDER = list(_SCREEN_TO_MENU_COL.keys())
_MENU_COLS = [_SCREEN_TO_MENU_COL[s] for s in _ORDER]


def _norm(s):
    return " ".join((s or "").strip().lower().split())


class Command(BaseCommand):
    help = "menu_user_relation'dan AccessLevel ve mevcut kullanici yetkilerini senkronlar."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Hicbir sey yazma, sadece raporla.")

    def handle(self, *args, **opts):
        from authorization.models import AccessLevel, Screen
        from accounts.models import User

        dry = opts["dry_run"]
        log = self.stdout.write

        # --- 1) Screen'leri yukle (kod -> Screen) ---
        screens = {s.code: s for s in Screen.objects.all()}
        missing = [c for c in _ORDER + [_ALWAYS_SCREEN] if c not in screens]
        if missing:
            log(self.style.ERROR(f"Eksik Screen kodlari: {missing}. Once seed calistir."))
            return

        # --- 2) menu_user_relation: employee_name -> kombinasyon imzasi ---
        # imza = 9 haneli '0/1' string (sadece eslenen 9 ekran).
        emp_to_sig = {}       # norm(employee_name) -> signature
        sig_counts = {}       # signature -> kac kisi
        with connections["refdb"].cursor() as cur:
            cur.execute(
                f"SELECT employee_name, {', '.join(_MENU_COLS)} "
                f"FROM solgar_org.menu_user_relation"
            )
            for row in cur.fetchall():
                name = row[0]
                bits = row[1:]
                sig = "".join("1" if (b and int(b) == 1) else "0" for b in bits)
                emp_to_sig[_norm(name)] = sig
                sig_counts[sig] = sig_counts.get(sig, 0) + 1

        log(f"menu_user_relation: {len(emp_to_sig)} calisan, "
            f"{len(sig_counts)} benzersiz kombinasyon.")

        # --- 3) email -> employee_name koprusu (employees) ---
        email_to_name = {}
        with connections["refdb"].cursor() as cur:
            cur.execute(
                "SELECT EMPLOYEE_EMAIL, EMPLOYEE_NAME FROM solgar_org.employees "
                "WHERE EMPLOYEE_EMAIL IS NOT NULL AND EMPLOYEE_EMAIL <> ''"
            )
            for email, name in cur.fetchall():
                e = _norm(email)
                if e and "@" in e and e not in email_to_name:
                    email_to_name[e] = _norm(name)

        # --- 4) AccessLevel'leri olustur/guncelle (her benzersiz kombinasyon) ---
        # rank: kisi sayisina gore (cok kisi = dusuk rank). Ad: ekran kisa adlari.
        sigs_sorted = sorted(sig_counts.items(), key=lambda kv: -kv[1])
        sig_to_level = {}   # signature -> AccessLevel (ya da dry'de ad)
        created_n = updated_n = 0
        rank = 1
        for sig, cnt in sigs_sorted:
            on_screens = [_ORDER[i] for i, c in enumerate(sig) if c == "1"]
            if on_screens:
                label = ", ".join(_SCREEN_SHORT[s] for s in on_screens)
            else:
                label = "Нет доступа"
            # ayni ada sahip baska kombinasyon olmasin diye imzayi da ekle (kisa)
            name = f"{label}"[:78]
            if not dry:
                lvl, created = AccessLevel.objects.get_or_create(
                    name=name, defaults={"rank": rank,
                                         "description": f"auto: menu sig {sig}"})
                # ekranlari ayarla: eslenen + FAQ (herkese acik)
                codes = on_screens + [_ALWAYS_SCREEN]
                lvl.screens.set([screens[c] for c in codes])
                if lvl.rank != rank:
                    lvl.rank = rank; lvl.save(update_fields=["rank"])
                sig_to_level[sig] = lvl
                created_n += 1 if created else 0
                updated_n += 0 if created else 1
            else:
                sig_to_level[sig] = name
            rank += 1

        log(f"AccessLevel: {len(sigs_sorted)} seviye "
            f"({'DRY' if dry else f'olusturulan {created_n}, guncellenen {updated_n}'}).")

        # --- 5) Mevcut platform kullanicilarina ata ---
        assigned = skipped = 0
        details = []
        for u in User.objects.all():
            if u.is_superuser:
                skipped += 1
                details.append(f"  [atlandi: superuser] {u.email}")
                continue
            ename = email_to_name.get(_norm(u.email))
            if not ename:
                skipped += 1
                details.append(f"  [atlandi: email employees'te yok] {u.email}")
                continue
            sig = emp_to_sig.get(ename)
            if sig is None:
                skipped += 1
                details.append(f"  [atlandi: menu'de yok] {u.email} ({ename})")
                continue
            lvl = sig_to_level.get(sig)
            if dry:
                details.append(f"  [atanacak] {u.email} -> {lvl}")
                assigned += 1
            else:
                u.access_level = lvl
                u.save(update_fields=["access_level"])
                details.append(f"  [atandi] {u.email} -> {lvl.name}")
                assigned += 1

        log(f"Kullanici atama: {assigned} atandi, {skipped} atlandi "
            f"(toplam {User.objects.count()} User).")
        for d in details:
            log(d)

        if dry:
            log(self.style.WARNING("DRY-RUN: hicbir sey yazilmadi."))
        else:
            log(self.style.SUCCESS("Senkron tamamlandi."))
