import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from backend.database import get_db, DB_PATH, seed_sample_data, init_db
from backend.models import AyarlarUpdate

router = APIRouter(prefix="/api/ayarlar", tags=["Ayarlar"])

@router.get("")
def get_ayarlar():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ayarlar WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

@router.put("")
def update_ayarlar(data: AyarlarUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ayarlar SET
            firma_adi = ?, yetkili = ?, vergi_dairesi = ?, vergi_no = ?,
            tckn = ?, telefon = ?, eposta = ?, web = ?, adres = ?,
            varsayilan_iban = ?, varsayilan_banka = ?, fatura_notu = ?
        WHERE id = 1
    """, (
        data.firma_adi, data.yetkili, data.vergi_dairesi, data.vergi_no,
        data.tckn, data.telefon, data.eposta, data.web, data.adres,
        data.varsayilan_iban, data.varsayilan_banka, data.fatura_notu
    ))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Firma ayarları başarıyla güncellendi."}

@router.get("/yedekle")
def yedek_indir():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Veritabanı dosyası bulunamadı.")
    return FileResponse(
        path=DB_PATH,
        filename="on_muhasebe_yedek.db",
        media_type="application/octet-stream"
    )

@router.post("/yedek-yukle")
async def yedek_yukle(file: UploadFile = File(...)):
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir .db uzantılı SQLite veritabanı dosyası seçiniz.")
    
    from datetime import datetime
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    
    # 1. Güvenlik için mevcut DB'nin yedeğini al
    if os.path.exists(DB_PATH):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"muhasebe_oncesi_otomatik_{ts}.db"
        shutil.copy2(DB_PATH, os.path.join(db_dir, backup_name))
        
    # 2. Yeni dosyayı yaz
    contents = await file.read()
    with open(DB_PATH, "wb") as f:
        f.write(contents)
        
    return {"success": True, "message": "Veritabanı yedeği başarıyla geri yüklendi! Sayfa yenilenecektir."}

@router.post("/ornek-veri-yukle")
def load_sample_data():
    try:
        seed_sample_data()
        return {"success": True, "message": "Örnek veriler başarıyla yüklendi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verileri-sifirla")
def verileri_sifirla(tumunu_temizle: bool = True):
    """
    Tüm hareket verilerini (faturalar, kasa/banka hareketleri, çekler) ve isteğe bağlı carileri sıfırlar.
    İşlem öncesi otomatik güvenlik yedeği alır.
    """
    try:
        from datetime import datetime
        db_dir = os.path.dirname(DB_PATH)
        os.makedirs(db_dir, exist_ok=True)
        
        # 1. Önce otomatik güvenlik yedeği al
        if os.path.exists(DB_PATH):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            yedek_dir = os.path.join(db_dir, "yedekler")
            os.makedirs(yedek_dir, exist_ok=True)
            shutil.copy2(DB_PATH, os.path.join(yedek_dir, f"sifirlama_oncesi_otomatik_{ts}.db"))

        conn = get_db()
        cursor = conn.cursor()
        
        # Foreign key kısıtlamalarını geçici kapatıp temizleme yap
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        cursor.execute("DELETE FROM fatura_kalemleri;")
        cursor.execute("DELETE FROM faturalar;")
        cursor.execute("DELETE FROM cari_hareketler;")
        cursor.execute("DELETE FROM kasa_banka_hareketleri;")
        cursor.execute("DELETE FROM cekler;")
        
        if tumunu_temizle:
            cursor.execute("DELETE FROM cariler;")
            cursor.execute("DELETE FROM stoklar;")
        else:
            cursor.execute("UPDATE cariler SET borc = 0.0, alacak = 0.0, bakiye = 0.0;")
            
        cursor.execute("UPDATE kasalar SET bakiye = 0.0;")
        cursor.execute("UPDATE bankalar SET bakiye = 0.0;")
        
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Tüm hareket ve örnek veriler başarıyla temizlendi! Tertemiz bir başlangıç yapabilirsiniz."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kapat")
def programi_kapat():
    """Masaüstü uygulamasını ve yerel sunucuyu güvenli şekilde kapatır."""
    import threading
    import time
    def _exit_later():
        time.sleep(0.4)
        os._exit(0)
    threading.Thread(target=_exit_later, daemon=True).start()
    return {"success": True, "message": "Program güvenle kapatılıyor..."}
