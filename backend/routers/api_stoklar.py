from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.models import StokCreate, StokUpdate
from backend.services import stok_service

router = APIRouter(prefix="/api/stoklar", tags=["Stok & Hizmet"])

@router.get("")
def get_stoklar(
    tip: Optional[str] = None,
    search: Optional[str] = None,
    sadece_kritik: bool = False
):
    return stok_service.list_stoklar(tip=tip, search=search, sadece_kritik=sadece_kritik)

@router.post("")
def add_stok(data: StokCreate):
    try:
        return stok_service.create_stok(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{stok_id}")
def get_single_stok(stok_id: int):
    stok = stok_service.get_stok(stok_id)
    if not stok:
        raise HTTPException(status_code=404, detail="Stok kartı bulunamadı.")
    return stok

@router.put("/{stok_id}")
def update_existing_stok(stok_id: int, data: StokUpdate):
    try:
        return stok_service.update_stok(stok_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{stok_id}")
def delete_existing_stok(stok_id: int):
    try:
        stok_service.delete_stok(stok_id)
        return {"success": True, "message": "Stok/Hizmet kartı başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
