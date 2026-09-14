src = open('sales/api.py', encoding='utf-8').read()
marker = '# ==================== Eczane (parametrik parser) upload API'
idx = src.find(marker)
if idx == -1:
    print("HATA: marker yok")
else:
    # İlk marker'dan öncesini tut + ilk bloğu bir kez tut
    before = src[:idx]
    after = src[idx:]
    # after'da kaç kez var
    count = after.count('def pharmacy_upload_preview_api')
    print(f"Duplike sayısı: {count}")
    # Sadece ilk bloğu tut (bir sonraki marker'a kadar ya da sona kadar)
    # İkinci marker'ı bul
    second = after.find(marker, len(marker))
    if second != -1:
        first_block = after[:second]
        print("İkinci+ bloklar siliniyor")
        src = before + first_block
        open('sales/api.py', 'w', encoding='utf-8').write(src)
        print("Temizlendi. Kalan pharmacy_upload_preview_api:", src.count('def pharmacy_upload_preview_api'))
    else:
        print("Tek marker, duplike başka şekilde")