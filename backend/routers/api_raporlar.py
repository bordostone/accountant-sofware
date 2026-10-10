from typing import Optional
from fastapi import APIRouter, Query
from backend.services import rapor_service

router = APIRouter(prefix="/api/raporlar", tags=["Raporlar"])

@router.get("/dashboard")
def get_dashboard():
    return rapor_service.get_dashboard_summary()

@router.get("/kdv")
def get_kdv(baslangic: Optional[str] = None, bitis: Optional[str] = None):
    return rapor_service.get_kdv_raporu(baslangic, bitis)

@router.get("/faturalar")
def get_faturalar_raporu(
    baslangic: Optional[str] = None,
    bitis: Optional[str] = None,
    tur: str = Query("HEPSI", enum=["HEPSI", "SATIS", "ALIS"]),
    durum: str = Query("HEPSI", enum=["HEPSI", "BEKLIYOR", "KISMI", "ODENDI", "IPTAL"]),
    search: Optional[str] = None
):
    return rapor_service.get_faturalar_raporu(baslangic, bitis, tur, durum, search)

@router.get("/tahsilat-odeme")
def get_tahsilat_odeme_raporu(
    baslangic: Optional[str] = None,
    bitis: Optional[str] = None,
    islem_grubu: str = Query("HEPSI", enum=["HEPSI", "TAHSILAT", "ODEME", "VIRMAN"]),
    search: Optional[str] = None
):
    return rapor_service.get_tahsilat_odeme_raporu(baslangic, bitis, islem_grubu, search)

@router.get("/hesap-hareketleri")
def get_hesap_hareketleri_raporu(
    baslangic: Optional[str] = None,
    bitis: Optional[str] = None,
    hesap_secimi: str = "TUMU",
    search: Optional[str] = None
):
    return rapor_service.get_hesap_hareketleri_raporu(baslangic, bitis, hesap_secimi, search)

