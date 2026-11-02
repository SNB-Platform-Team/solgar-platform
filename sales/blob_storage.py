"""
Azure Blob Storage yardimcisi — ekipman (оборудование) fotograflari icin.

Ayarlar (App Settings / .env):
  AZURE_STORAGE_CONNECTION_STRING  -> storage account connection string
  AZURE_STORAGE_CONTAINER          -> container adi (default: equipment-photos)

Kullanim:
  from sales.blob_storage import upload_photo, delete_blob, blob_configured
  if blob_configured():
      name, url = upload_photo(file_bytes, "foto.jpg", content_type="image/jpeg")

Fotograflar container'da benzersiz isimle (uuid) saklanir; yuklenen dosya adi
blob adina DAHIL edilmez (çakisma/guvenlik). Donen 'name' DB'de tutulur, 'url'
dogrudan erisim icindir (container private ise URL tek basina yetmez; erisim
icin uygulama uzerinden SAS ya da proxy gerekir — bkz. not).
"""

from __future__ import annotations

import uuid
import os


def _conn_str() -> str:
    """Connection string'i ayarlardan al (settings get_secret ya da env)."""
    try:
        from django.conf import settings
        val = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", "") or ""
        if val:
            return val
    except Exception:
        pass
    return os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "") or ""


def _container_name() -> str:
    try:
        from django.conf import settings
        val = getattr(settings, "AZURE_STORAGE_CONTAINER", "") or ""
        if val:
            return val
    except Exception:
        pass
    return os.environ.get("AZURE_STORAGE_CONTAINER", "") or "equipment-photos"


def blob_configured() -> bool:
    """Blob kullanilabilir mi (connection string var mi)."""
    return bool(_conn_str())


def _client():
    """BlobServiceClient dondur (lazy import — paket yoksa anlasilir hata)."""
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(_conn_str())


def _container_client():
    cc = _client().get_container_client(_container_name())
    return cc


def upload_photo(data: bytes, original_name: str = "",
                 content_type: str = "application/octet-stream",
                 prefix: str = "equipment") -> tuple[str, str]:
    """
    Fotografi Blob'a yukle. (blob_name, url) dondurur.

    blob_name: container icindeki benzersiz ad (DB'de bu saklanir).
    url: blob'un tam URL'si (container private ise dogrudan acilmaz; erisim
         icin get_sas_url ya da proxy kullan).
    """
    # Uzanti orijinal addan (yoksa content_type'tan tahmin).
    ext = ""
    if original_name and "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[-1].lower()
    if not ext:
        import mimetypes
        ext = mimetypes.guess_extension(content_type or "") or ""
    blob_name = f"{prefix}/{uuid.uuid4().hex}{ext}"

    from azure.storage.blob import ContentSettings
    cc = _container_client()
    cc.upload_blob(
        name=blob_name,
        data=data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type or None),
    )
    bc = cc.get_blob_client(blob_name)
    return blob_name, bc.url


def download_blob(blob_name: str) -> tuple[bytes, str]:
    """Blob'u indir. (data, content_type) dondurur."""
    cc = _container_client()
    bc = cc.get_blob_client(blob_name)
    stream = bc.download_blob()
    data = stream.readall()
    ct = ""
    try:
        ct = stream.properties.content_settings.content_type or ""
    except Exception:
        ct = ""
    return data, (ct or "application/octet-stream")


def delete_blob(blob_name: str) -> bool:
    """Blob'u sil. Basarili ise True. (Zafer: silinen 7 gun geri alinabilir.)"""
    try:
        cc = _container_client()
        cc.delete_blob(blob_name)
        return True
    except Exception:
        return False


def get_sas_url(blob_name: str, minutes: int = 60) -> str:
    """
    Private container'daki bir blob icin gecici (SAS) okuma URL'si uret.
    Kullanici fotografi bu URL ile dogrudan gorebilir; sure dolunca gecersiz.
    """
    from datetime import datetime, timedelta, timezone
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions

    svc = _client()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    sas = generate_blob_sas(
        account_name=svc.account_name,
        container_name=_container_name(),
        blob_name=blob_name,
        account_key=svc.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
    )
    bc = _container_client().get_blob_client(blob_name)
    return f"{bc.url}?{sas}"
