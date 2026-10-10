from typing import List, Optional
from pydantic import BaseModel, Field

# --- CARİ MODELLERİ ---
class CariBase(BaseModel):
    unvan: str
    tip: str = "MUSTERI"  # MUSTERI, TEDARIKCI, HEPSI
    yetkili_kisi: Optional[str] = ""
    vergi_dairesi: Optional[str] = ""
    vergi_no: Optional[str] = ""
    tckn: Optional[str] = ""
    telefon: Optional[str] = ""
    eposta: Optional[str] = ""
    adres: Optional[str] = ""
    il: Optional[str] = ""
    ilce: Optional[str] = ""
    notlar: Optional[str] = ""
    is_personel: Optional[bool] = False
    personel_gorevi: Optional[str] = ""
    personel_departman: Optional[str] = ""

class CariCreate(CariBase):
    kod: Optional[str] = None
    acilis_bakiyesi: Optional[float] = 0.0
    acilis_bakiye_turu: Optional[str] = "BORC"  # BORC, ALACAK

class CariUpdate(CariBase):
    durum: Optional[str] = "AKTIF"

class CariHareketCreate(BaseModel):
    cari_id: int
    islem_turu: str = "BORC_DEKONTU"  # DEVIR, BORC_DEKONTU, ALACAK_DEKONTU
    tarih: str
    tutar: float
    evrak_no: Optional[str] = ""
    aciklama: str
    hareket_yonu: Optional[str] = "BORC"  # BORC, ALACAK (Devir için)

# --- STOK / HİZMET MODELLERİ ---
class StokBase(BaseModel):
    ad: str
    tip: str = "URUN"  # URUN, HIZMET
    birim: str = "Adet"
    alis_fiyati: float = 0.0
    satis_fiyati: float = 0.0
    kdv_orani: float = 20.0
    stok_miktari: float = 0.0
    kritik_stok: float = 5.0

class StokCreate(StokBase):
    kod: Optional[str] = None

class StokUpdate(StokBase):
    durum: Optional[str] = "AKTIF"

# --- FATURA MODELLERİ ---
class FaturaKalemIn(BaseModel):
    stok_id: Optional[int] = None
    aciklama: str
    miktar: float = 1.0
    birim: str = "Adet"
    birim_fiyat: float = 0.0
    kdv_orani: float = 20.0
    kdv_tutari: Optional[float] = None
    iskonto_orani: float = 0.0

class FaturaCreate(BaseModel):
    fatura_no: Optional[str] = None
    fatura_turu: str = "SATIS"  # SATIS, ALIS
    fatura_tarihi: str
    vade_tarihi: Optional[str] = None
    cari_id: int
    aciklama: Optional[str] = ""
    iskonto_orani: float = 0.0
    kdv_toplam: Optional[float] = None
    kalemler: List[FaturaKalemIn]

# --- KASA & BANKA MODELLERİ ---
class KasaCreate(BaseModel):
    kod: Optional[str] = None
    ad: str
    para_birimi: str = "TRY"
    aciklama: Optional[str] = ""

class BankaCreate(BaseModel):
    banka_adi: str
    sube_adi: Optional[str] = ""
    hesap_no: Optional[str] = ""
    iban: str
    para_birimi: str = "TRY"
    aciklama: Optional[str] = ""

class OdemeTahsilatCreate(BaseModel):
    islem_turu: str  # KASA_TAHSILAT, KASA_ODEME, BANKA_GELEN_HAVALE, BANKA_GIDEN_HAVALE, KASA_BANKA_VIRMAN, BANKA_KASA_VIRMAN
    tarih: str
    tutar: float
    kasa_id: Optional[int] = None
    banka_id: Optional[int] = None
    cari_id: Optional[int] = None
    fatura_id: Optional[int] = None
    aciklama: Optional[str] = ""
    evrak_no: Optional[str] = ""

# --- ÇEK MODELLERİ ---
class CekCreate(BaseModel):
    cek_turu: str = "ALINAN"  # ALINAN, VERILEN
    cek_no: str
    vade_tarihi: str
    giris_tarihi: Optional[str] = None
    tutar: float
    banka_adi: str
    sube_adi: Optional[str] = ""
    hesap_no: Optional[str] = ""
    kesideci: Optional[str] = ""
    cari_id: int
    aciklama: Optional[str] = ""

class CekDurumGuncelle(BaseModel):
    yeni_durum: str  # PORTFOYDE, BANKAYA_VERILDI, TAHSIL_EDILDI, CIROLANMIS, KARSILIKSIZ, IADE_EDILDI
    islem_tarihi: str
    kasa_id: Optional[int] = None
    banka_id: Optional[int] = None
    cirolanan_cari_id: Optional[int] = None
    aciklama: Optional[str] = ""

# --- AYARLAR MODELLERİ ---
class AyarlarUpdate(BaseModel):
    firma_adi: str
    yetkili: Optional[str] = ""
    vergi_dairesi: Optional[str] = ""
    vergi_no: Optional[str] = ""
    tckn: Optional[str] = ""
    telefon: Optional[str] = ""
    eposta: Optional[str] = ""
    web: Optional[str] = ""
    adres: Optional[str] = ""
    varsayilan_iban: Optional[str] = ""
    varsayilan_banka: Optional[str] = ""
    fatura_notu: Optional[str] = ""
