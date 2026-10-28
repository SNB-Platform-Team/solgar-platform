# -*- coding: utf-8 -*-
"""get_config + parse_chain'e country parametresi ekle; cakisan zincirleri ulke ile coz."""
import io
P = r'sales\pharmacy_all_configs.py'
s = io.open(P, encoding='utf-8').read()
changed = []

# 1) get_config imzasina country ekle + cakisma cozumu (en basta)
OLD_SIG = 'def get_config(chain_or_file):'
NEW_SIG = 'def get_config(chain_or_file, country=""):'
if OLD_SIG in s:
    s = s.replace(OLD_SIG, NEW_SIG, 1)
    changed.append("get_config imza")

# cakisma cozumu: nhay hesaplandiktan hemen sonra ulke-bazli override
# "nhay = _norm_key(chain_or_file)" satirindan sonra ekle
ANCH = 'nhay = _norm_key(chain_or_file)'
OVERRIDE = '''nhay = _norm_key(chain_or_file)
    # --- Ulke-bazli cakisma cozumu ---
    _cu = (country or "").strip().lower()
    # VITA: Kazakistan'da c1 (Номенклатура ic ice), Rusya'da VITA+/VITA_SAMARA/VITA_TOMSK ayri
    if "VITA" in nhay and _cu in ("russia", "россия", "rusya"):
        # Rusya ise KZ VITA (c1) ile eslesmeyi engelle: c1 VITA'yi atla
        for key, cfg in SIMPLE_CONFIGS.items():
            if _norm_key(key) in nhay and "VITA" in _norm_key(key):
                return cfg, "simple"
    # ASNA: Kazakistan'da matrix, Rusya'da simple
    if "ASNA" in nhay:
        if _cu in ("russia","россия","rusya"):
            for key, cfg in SIMPLE_CONFIGS.items():
                if _norm_key(key) == "ASNA":
                    return cfg, "simple"
        else:
            if "ASNA" in MATRIX_CONFIGS:
                return MATRIX_CONFIGS["ASNA"], "matrix"'''
if ANCH in s and "Ulke-bazli cakisma" not in s:
    s = s.replace(ANCH, OVERRIDE, 1)
    changed.append("cakisma override")

# 2) parse_chain imzasina country ekle + get_config'e gecir
OLD_PC = 'def parse_chain(sheet, chain_or_file, main_group, v_limit, h_limit):'
NEW_PC = 'def parse_chain(sheet, chain_or_file, main_group, v_limit, h_limit, country=""):'
if OLD_PC in s:
    s = s.replace(OLD_PC, NEW_PC, 1); changed.append("parse_chain imza")

OLD_GC2 = 'cfg, typ = get_config(chain_or_file)'
NEW_GC2 = 'cfg, typ = get_config(chain_or_file, country)'
if OLD_GC2 in s:
    s = s.replace(OLD_GC2, NEW_GC2, 1); changed.append("parse_chain get_config cagri")

io.open(P,'w',encoding='utf-8').write(s)
print("DEGISENLER:", changed)