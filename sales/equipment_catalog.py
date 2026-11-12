"""
Оборудование (ekipman) DEMO katalogu — promo must-have kontrolu + POS imidj
listeleri. Hepsi kodda sabit (demo); gorseller FRONTEND repo'sunda static olarak
durur, backend yalniz imidj ADLARINI ve must-have bilgisini bilir.

- EQUIPMENT_PROMOS: secilebilir promo (оборудование) listesi. Brand'e gore ayni
  (Olga: Solgar ve Bounty icin promo listesi ozdes).
- PROMO_REQUIRES_IMIDZH: promo 'must have имидж' mi? (solgar_cor.presence_image
  tablosunun presence_image=1 satirlarinin kodda sabit kopyasi). Olga:
  СТОЙКИ=Стойка, КОВРИК=Брендированный коврик AYNI sey. Eslesme normalize
  (buyuk harf + bosluk sadelestirme) ile yapilir; boylece 'СТОЙКИ'/'Стойка',
  'ПЛАКАТ'/'Плакат' gibi varyasyonlar tutar.
- POS_IMAGES_SL / POS_IMAGES_NB: brand'e gore secilebilecek imidj (POS gorseli)
  ADLARI. Frontend bu adlari gorsele cevirir (ad -> static dosya).
"""

from __future__ import annotations


def _norm(s: str) -> str:
    """Promo adini eslesme icin normalize et: buyuk harf, ic bosluklari tek
    bosluga indir, bas/son bosluk at. 'Брендированный' on eki ve tekil/cogul
    farki icin PROMO_ALIASES kullanilir (asagida)."""
    return " ".join((s or "").strip().upper().split())


# оборудование promo listesi (Solgar = Bounty, ozdes). Dropdown bu sirayla.
EQUIPMENT_PROMOS = [
    "3Д БАНКА",
    "АНТИКРАЖНЫЕ ВОРОТА",
    "КАТАЛОЖНИЦА",
    "КОВРИК",
    "КОРНЕР",
    "ЛАЙТБОКС",
    "ОСВЕЩЕНИЕ ВЫКЛАДКИ",
    "ПЛАКАТ",
    "РОЛЛ-АП",
    "СТОЙКИ",
    "ХАРДПОСТЕР",
]

# presence_image=1 (имидж ZORUNLU) olan promo'lar — normalize edilmis anahtarla.
# solgar_cor.presence_image'den: Ролл-ап, Лайтбокс, Антикражные ворота, Плакат.
_MUST_HAVE_NORM = {
    _norm("РОЛЛ-АП"),
    _norm("ЛАЙТБОКС"),
    _norm("АНТИКРАЖНЫЕ ВОРОТА"),
    _norm("ПЛАКАТ"),
}


def promo_requires_imidzh(promo: str) -> bool:
    """Bu promo 'must have имидж' mi? (presence_image=1). Normalize eslesme."""
    return _norm(promo) in _MUST_HAVE_NORM


# POS имидж adlari — SOLGAR (POS_SL). Frontend ad -> static gorsel esler.
POS_IMAGES_SL = [
    "Kангавитес, комплекс мультивитаминов и минералов",
    "Время позаботиться о своей красоте Кожа, ногти, волосы",
    "Глицинат магния",
    "Ежедневный заряд энергии Мультиван",
    "Комплекс коллагена и гиалуроновой кислоты",
    "Нейронутриентс",
    "Нужна энергия как у ребенка Цитрат магния",
    "Омега-комплекс из дикого океанического лосося",
    "Полина Аскери Антиоксидантная формула",
    "Полина Аскери Цитрат магния (порошок)",
    "Полина Аскери Эстер-С плюс витамин С 500 мг",
    "Порошок цитрат магния",
    "Тройная Омега-3 950 мг ЭПК и ДГК",
    "Хотите проверить свои физические способности Тройная Омега-3 950 мг ЭПК и ДГК",
    "Хотите фото без фильтров Кожа, ногти, волосы",
    "Цените золотые моменты Кангавитес, комплекс мультивитаминов и минералов",
    "Эстер-С с витамином С 500 мг",
]

# POS имидж adlari — NATURE'S BOUNTY (POS_NB).
POS_IMAGES_NB = [
    "Oмега-3 из морских водорослей",
    "Ацидофилус Пробиотик",
    "Гидролизованный коллаген с витамином С",
    "Глицинат магния",
    "Кальций Магний Цинк",
    "Коэнзим Q10 100 мг",
    "Мультидэй с экстрактом листьев зеленого чая",
    "Рыбий жир 1000 мг Омега-3",
    "Цитрат магния с витамином В6",
    "Эстер-С 500 мг",
]


def pos_images_for_brand(brand: str) -> list[str]:
    """Brand'e gore POS имидж ad listesi. BOUNTY -> NB, aksi -> SL."""
    b = (brand or "").strip().upper()
    if "BOUNTY" in b or b == "BN" or "NB" == b:
        return list(POS_IMAGES_NB)
    return list(POS_IMAGES_SL)


# E-posta alan adindan brand: @naturesbounty.* -> BOUNTY, aksi -> SOLGAR.
def brand_from_email(email: str) -> str:
    """Kullanicinin e-posta alan adindan brand belirle. Olga: Solgar hesaplari
    ornek@solgarvitamin.ru, Bounty hesaplari ornek@naturesbounty.ru."""
    e = (email or "").strip().lower()
    if "@naturesbounty" in e or "naturesbounty." in e:
        return "BOUNTY"
    return "SOLGAR"
