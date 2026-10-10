from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.models import CariCreate, CariUpdate, CariHareketCreate
from backend.services import cari_service

router = APIRouter(prefix="/api/cariler", tags=["Cariler"])

@router.get("")
def get_cariler(
    tip: Optional[str] = None,
    bakiye_durumu: Optional[str] = None,
    sort_by: Optional[str] = "unvan_asc",
    search: Optional[str] = None,
    durum: Optional[str] = None
):
    return cari_service.list_cariler(tip=tip, search=search, durum=durum, bakiye_durumu=bakiye_durumu, sort_by=sort_by)

@router.post("")
def add_cari(data: CariCreate):
    try:
        return cari_service.create_cari(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{cari_id}")
def get_single_cari(cari_id: int):
    cari = cari_service.get_cari(cari_id)
    if not cari:
        raise HTTPException(status_code=404, detail="Cari kart bulunamadı.")
    return cari

@router.put("/{cari_id}")
def update_existing_cari(cari_id: int, data: CariUpdate):
    try:
        return cari_service.update_cari(cari_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{cari_id}")
def remove_cari(cari_id: int):
    try:
        cari_service.delete_cari(cari_id)
        return {"success": True, "message": "Cari başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{cari_id}/ekstre")
def get_ekstre(
    cari_id: int,
    baslangic_tarihi: Optional[str] = Query(None),
    bitis_tarihi: Optional[str] = Query(None)
):
    ekstre = cari_service.get_cari_ekstre(cari_id, baslangic_tarihi, bitis_tarihi)
    if not ekstre:
        raise HTTPException(status_code=404, detail="Cari bulunamadı.")
    return ekstre

@router.post("/hareket")
def add_hareket(data: CariHareketCreate):
    try:
        return cari_service.add_cari_hareket(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hareket/{hareket_id}")
def get_hareket_by_id(hareket_id: int):
    h = cari_service.get_cari_hareket(hareket_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hareket kaydı bulunamadı.")
    return h

@router.put("/hareket/{hareket_id}")
def update_hareket(hareket_id: int, data: CariHareketCreate):
    try:
        return cari_service.update_cari_hareket(hareket_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/hareket/{hareket_id}")
def delete_hareket(hareket_id: int):
    try:
        cari_service.delete_cari_hareket(hareket_id)
        return {"success": True, "message": "Hareket başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


