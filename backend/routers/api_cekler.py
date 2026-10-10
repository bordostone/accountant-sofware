from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.models import CekCreate, CekDurumGuncelle
from backend.services import cek_service

router = APIRouter(prefix="/api/cekler", tags=["Çek Takibi"])

@router.get("")
def get_cekler(
    cek_turu: Optional[str] = None,
    durum: Optional[str] = None,
    search: Optional[str] = None
):
    return cek_service.list_cekler(cek_turu=cek_turu, durum=durum, search=search)

@router.post("")
def add_cek(data: CekCreate):
    try:
        return cek_service.create_cek(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{cek_id}")
def get_single_cek(cek_id: int):
    cek = cek_service.get_cek(cek_id)
    if not cek:
        raise HTTPException(status_code=404, detail="Çek bulunamadı.")
    return cek

@router.post("/{cek_id}/durum")
def change_cek_durumu(cek_id: int, data: CekDurumGuncelle):
    try:
        return cek_service.update_cek_durumu(cek_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{cek_id}")
def delete_existing_cek(cek_id: int):
    try:
        cek_service.delete_cek(cek_id)
        return {"success": True, "message": "Çek kaydı başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
