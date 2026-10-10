import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, seed_sample_data
from backend.routers import (
    api_cariler,
    api_faturalar,
    api_kasa_banka,
    api_cekler,
    api_stoklar,
    api_raporlar,
    api_ayarlar
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken veritabanı tablolarını hazırla (varsa dokunmaz)
    init_db()
    yield

app = FastAPI(
    title="Ön Muhasebe Pro",
    description="Fatura, Kasa, Banka, Çek ve Cari Hesap Yönetim Platformu",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(api_cariler.router)
app.include_router(api_faturalar.router)
app.include_router(api_kasa_banka.router)
app.include_router(api_cekler.router)
app.include_router(api_stoklar.router)
app.include_router(api_raporlar.router)
app.include_router(api_ayarlar.router)

# Statik dosyaları bağla
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Ön Muhasebe Pro Backend API Çalışıyor. static/index.html hazırlanıyor."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
