from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.models import KasaCreate, BankaCreate, OdemeTahsilatCreate
from backend.services import kasa_banka_service

router = APIRouter(prefix="/api/kasa-banka", tags=["Kasa & Banka"])

@router.get("/kasalar")
def get_kasalar():
    return kasa_banka_service.list_kasalar()

@router.get("/kasalar/{kasa_id}")
def get_single_kasa(kasa_id: int):
    k = kasa_banka_service.get_kasa(kasa_id)
    if not k:
        raise HTTPException(status_code=404, detail="Kasa bulunamadı.")
    return k

@router.post("/kasalar")
def add_kasa(data: KasaCreate):
    try:
        return kasa_banka_service.create_kasa(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/kasalar/{kasa_id}")
def update_kasa(kasa_id: int, data: KasaCreate):
    try:
        return kasa_banka_service.update_kasa(kasa_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/kasalar/{kasa_id}")
def delete_kasa(kasa_id: int):
    try:
        kasa_banka_service.delete_kasa(kasa_id)
        return {"success": True, "message": "Kasa başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bankalar")
def get_bankalar():
    return kasa_banka_service.list_bankalar()

@router.get("/bankalar/{banka_id}")
def get_single_banka(banka_id: int):
    b = kasa_banka_service.get_banka(banka_id)
    if not b:
        raise HTTPException(status_code=404, detail="Banka hesabı bulunamadı.")
    return b

@router.post("/bankalar")
def add_banka(data: BankaCreate):
    try:
        return kasa_banka_service.create_banka(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/bankalar/{banka_id}")
def update_banka(banka_id: int, data: BankaCreate):
    try:
        return kasa_banka_service.update_banka(banka_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/bankalar/{banka_id}")
def delete_banka(banka_id: int):
    try:
        kasa_banka_service.delete_banka(banka_id)
        return {"success": True, "message": "Banka hesabı başarıyla silindi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hareketler")
def get_hareketler(
    islem_turu: Optional[str] = None,
    cari_id: Optional[int] = None,
    kasa_id: Optional[int] = None,
    banka_id: Optional[int] = None,
    baslangic: Optional[str] = None,
    bitis: Optional[str] = None
):
    return kasa_banka_service.list_hareketler(
        islem_turu=islem_turu,
        cari_id=cari_id,
        kasa_id=kasa_id,
        banka_id=banka_id,
        baslangic=baslangic,
        bitis=bitis
    )

@router.post("/islem")
def make_islem(data: OdemeTahsilatCreate):
    try:
        return kasa_banka_service.create_islem(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hareketler/{hareket_id}")
def get_single_hareket(hareket_id: int):
    h = kasa_banka_service.get_hareket(hareket_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hareket bulunamadı.")
    return h

@router.put("/hareketler/{hareket_id}")
def update_existing_islem(hareket_id: int, data: OdemeTahsilatCreate):
    try:
        return kasa_banka_service.update_islem(hareket_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/hareketler/{hareket_id}")
def delete_existing_islem(hareket_id: int):
    try:
        kasa_banka_service.delete_islem(hareket_id)
        return {"success": True, "message": "Hareket başarıyla silindi ve bakiyeler güncellendi."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

