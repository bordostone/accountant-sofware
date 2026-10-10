from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.models import FaturaCreate
from backend.services import fatura_service

router = APIRouter(prefix="/api/faturalar", tags=["Faturalar"])

@router.get("")
def get_faturalar(
    fatura_turu: Optional[str] = None,
    cari_id: Optional[int] = None,
    odeme_durumu: Optional[str] = None,
    search: Optional[str] = None
):
    return fatura_service.list_faturalar(
        fatura_turu=fatura_turu,
        cari_id=cari_id,
        odeme_durumu=odeme_durumu,
        search=search
    )

@router.post("")
def add_fatura(data: FaturaCreate):
    try:
        return fatura_service.create_fatura(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{fatura_id}")
def get_single_fatura(fatura_id: int):
    fatura = fatura_service.get_fatura(fatura_id)
    if not fatura:
        raise HTTPException(status_code=404, detail="Fatura bulunamadı.")
    return fatura

@router.put("/{fatura_id}")
def update_existing_fatura(fatura_id: int, data: FaturaCreate):
    try:
        return fatura_service.update_fatura(fatura_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{fatura_id}/iptal")
def cancel_existing_fatura(fatura_id: int):
    try:
        fatura_service.cancel_fatura(fatura_id)
        return {"success": True, "message": "Fatura başarıyla iptal edildi ve hareketler geri alındı."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{fatura_id}")
def delete_existing_fatura(fatura_id: int):
    try:
        fatura_service.delete_fatura(fatura_id)
        return {"success": True, "message": "Fatura ve bağlı hareketleri başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
