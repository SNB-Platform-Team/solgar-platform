src = open('sales/depo_storage_parser.py', encoding='utf-8').read()
old = '''        return "" if val is None else str(val)'''
new = '''        if val is None:
            return ""
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val)'''
if old in src:
    src = src.replace(old, new)
    open('sales/depo_storage_parser.py', 'w', encoding='utf-8').write(src)
    print("Duzeltildi")
else:
    print("Eski satir bulunamadi - dosya zaten farkli, kontrol lazim")