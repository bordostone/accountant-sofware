#!/usr/bin/env python3
"""
Ön Muhasebe Pro - Windows Çevrimdışı (Offline) Kurulum & Dağıtım Paketi Üretici
Bu script:
1. Resmi Windows 64-bit gömülü Python çalışma ortamını (Python Embeddable) indirir ve yapılandırır.
2. Microsoft Visual C++ 2015-2022 Redistributable paketini (VC_redist.x64.exe) çevrimdışı kurulum için dahil eder.
3. FastAPI, Uvicorn, Pydantic ve tüm bağımlılıkların Windows x64 binary tekerleklerini (wheels) site-packages içine açar.
4. Proje dosyalarını, statik web arayüzünü ve veritabanı şablonunu kopyalar.
5. Windows CRLF (\r\n) uyumlu başlatıcıları (Baslat.bat, Baslat_Sessiz.vbs, Durdur.bat, Teshis.bat),
   masaüstü kısayol oluşturucuyu (kisayol_olustur.vbs) ve kurulum sihirbazını (Kurulum.bat, setup.iss) üretir.
6. Windows için çoklu çözünürlüklü özel simge (app.ico) oluşturur.
7. Son olarak her şeyi tek bir taşınabilir ZIP arşivi olarak paketler.
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
import struct

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist_windows")
APP_DIR = os.path.join(DIST_DIR, "OnMuhasebePro")
PYTHON_DIR = os.path.join(APP_DIR, "python")
SITE_PACKAGES_DIR = os.path.join(PYTHON_DIR, "Lib", "site-packages")
CACHE_DIR = "/tmp/onmuhasebe_build_cache"

PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
PYTHON_EMBED_ZIP = os.path.join(CACHE_DIR, "python-3.11.9-embed-amd64.zip")
VCREDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
VCREDIST_EXE = os.path.join(CACHE_DIR, "VC_redist.x64.exe")
WHEELS_DIR = os.path.join(CACHE_DIR, "wheels_win64")

def log(msg):
    print(f"[BUILD] {msg}")

def ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(WHEELS_DIR, exist_ok=True)

def download_python_embed():
    if os.path.exists(PYTHON_EMBED_ZIP) and os.path.getsize(PYTHON_EMBED_ZIP) > 5_000_000:
        log("Python embed zip önbellekte mevcut.")
        return
    if os.path.exists("/tmp/python-3.11.9-embed-amd64.zip") and os.path.getsize("/tmp/python-3.11.9-embed-amd64.zip") > 5_000_000:
        shutil.copy2("/tmp/python-3.11.9-embed-amd64.zip", PYTHON_EMBED_ZIP)
        log("Python embed zip /tmp konumundan alındı.")
        return
    log(f"Windows Python 3.11.9 Embeddable indiriliyor: {PYTHON_EMBED_URL}...")
    subprocess.check_call(["curl", "-sSL", "-o", PYTHON_EMBED_ZIP, PYTHON_EMBED_URL])
    log(f"İndirildi: {os.path.getsize(PYTHON_EMBED_ZIP):,} bayt")

def download_vcredist():
    if os.path.exists(VCREDIST_EXE) and os.path.getsize(VCREDIST_EXE) > 20_000_000:
        log("VC_redist.x64.exe önbellekte mevcut.")
        return
    if os.path.exists("/tmp/VC_redist.x64.exe") and os.path.getsize("/tmp/VC_redist.x64.exe") > 20_000_000:
        shutil.copy2("/tmp/VC_redist.x64.exe", VCREDIST_EXE)
        log("VC_redist.x64.exe /tmp konumundan alındı.")
        return
    log(f"Microsoft Visual C++ Redistributable indiriliyor: {VCREDIST_URL}...")
    subprocess.check_call(["curl", "-sSL", "-o", VCREDIST_EXE, VCREDIST_URL])
    log(f"İndirildi: {os.path.getsize(VCREDIST_EXE):,} bayt")

def download_windows_wheels():
    packages = ["fastapi", "uvicorn", "pydantic", "python-multipart", "colorama"]
    log("Windows x64 tekerlekleri (wheels) indiriliyor...")
    pip_cmd = [
        sys.executable, "-m", "pip", "download",
        "--only-binary=:all:",
        "--platform", "win_amd64",
        "--python-version", "3.11",
        "--dest", WHEELS_DIR
    ] + packages
    subprocess.check_call(pip_cmd)
    log(f"Tekerlekler indirildi ({len(os.listdir(WHEELS_DIR))} dosya).")

def create_app_ico(output_path):
    """Saf Python ile çoklu çözünürlüklü (16, 32, 48, 64) Windows .ico dosyası üretir."""
    sizes = [16, 32, 48, 64]
    entries = []
    images = []
    offset = 6 + 16 * len(sizes)

    for s in sizes:
        img_bytes = bytearray()
        img_bytes += struct.pack('<IIIHHIIIIII', 40, s, s * 2, 1, 32, 0, s * s * 4, 0, 0, 0, 0)

        for y in range(s):
            for x in range(s):
                ratio_y = y / float(s)
                r = int(30 + ratio_y * 40)
                g = int(58 + ratio_y * 30)
                b = int(138 + ratio_y * 85)
                a = 255

                if (x < 2 and y < 2) or (x >= s - 2 and y < 2) or (x < 2 and y >= s - 2) or (x >= s - 2 and y >= s - 2):
                    if s >= 32:
                        a = 0

                nx = x / float(s)
                ny = (s - 1 - y) / float(s)

                in_m = False
                if 0.22 <= ny <= 0.78:
                    if 0.20 <= nx <= 0.30:
                        in_m = True
                    elif 0.70 <= nx <= 0.80:
                        in_m = True
                    elif 0.30 < nx <= 0.50 and abs((nx - 0.30) - (ny - 0.22) * 1.1) < 0.10:
                        in_m = True
                    elif 0.50 < nx < 0.70 and abs((0.70 - nx) - (ny - 0.22) * 1.1) < 0.10:
                        in_m = True

                if in_m and a > 0:
                    r, g, b = 255, 255, 255

                img_bytes += struct.pack('BBBB', b, g, r, a)

        row_bytes = (s + 31) // 32 * 4
        and_mask = b'\x00' * (row_bytes * s)
        img_bytes += and_mask

        images.append(img_bytes)
        w = 0 if s == 256 else s
        h = 0 if s == 256 else s
        entries.append(struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(img_bytes), offset))
        offset += len(img_bytes)

    with open(output_path, 'wb') as f:
        f.write(struct.pack('<HHH', 0, 1, len(sizes)))
        for e in entries:
            f.write(e)
        for img in images:
            f.write(img)

def assemble_distribution():
    log("Dağıtım klasörü hazırlanıyor...")
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(PYTHON_DIR, exist_ok=True)
    os.makedirs(SITE_PACKAGES_DIR, exist_ok=True)

    # 1. Python embed aç
    log("Python gömülü ortamı açılıyor...")
    with zipfile.ZipFile(PYTHON_EMBED_ZIP, 'r') as zf:
        zf.extractall(PYTHON_DIR)

    # 2. python311._pth düzenle (Windows CRLF ile)
    pth_file = os.path.join(PYTHON_DIR, "python311._pth")
    with open(pth_file, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("python311.zip\r\n.\r\nLib\\site-packages\r\n..\r\nimport site\r\n")

    # 3. Tekerlekleri (wheels) site-packages içine aç
    log("Kütüphaneler (FastAPI, Uvicorn, Pydantic vb.) site-packages içine kuruluyor...")
    for whl in os.listdir(WHEELS_DIR):
        if whl.endswith(".whl"):
            whl_path = os.path.join(WHEELS_DIR, whl)
            with zipfile.ZipFile(whl_path, 'r') as zf:
                zf.extractall(SITE_PACKAGES_DIR)

    # 4. Proje kodlarını kopyala
    log("Uygulama kaynak kodları ve statik dosyalar kopyalanıyor...")
    shutil.copytree(os.path.join(PROJECT_ROOT, "backend"), os.path.join(APP_DIR, "backend"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(os.path.join(PROJECT_ROOT, "static"), os.path.join(APP_DIR, "static"), ignore=shutil.ignore_patterns(".DS_Store"))
    shutil.copy2(os.path.join(PROJECT_ROOT, "main.py"), os.path.join(APP_DIR, "main.py"))

    # 5. Veritabanı klasörünü ve temiz SQLite şablonunu oluştur
    data_dir = os.path.join(APP_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    src_db = os.path.join(PROJECT_ROOT, "data", "muhasebe.db")
    if os.path.exists(src_db):
        shutil.copy2(src_db, os.path.join(data_dir, "muhasebe.db"))

    # 5.1 Redist klasörü ve VC_redist.x64.exe kopyala
    redist_dir = os.path.join(APP_DIR, "redist")
    os.makedirs(redist_dir, exist_ok=True)
    if os.path.exists(VCREDIST_EXE):
        shutil.copy2(VCREDIST_EXE, os.path.join(redist_dir, "VC_redist.x64.exe"))

    # 6. Simgeleri üret
    ico_path = os.path.join(APP_DIR, "app.ico")
    create_app_ico(ico_path)
    shutil.copy2(ico_path, os.path.join(APP_DIR, "static", "favicon.ico"))

    # 7. run.py oluştur (Korumalı, pythonw-uyumlu ve çökme-önleyici, Windows CRLF)
    run_py_content = '''# -*- coding: utf-8 -*-
"""
Özerler Mermer - Ön Muhasebe Pro
Windows Bağımsız Çalışma ve Başlatıcı Giriş Noktası
"""
import os
import sys
import time
import socket
import atexit
import copy
import threading
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

site_packages = os.path.join(ROOT_DIR, "python", "Lib", "site-packages")
if os.path.exists(site_packages) and site_packages not in sys.path:
    sys.path.insert(0, site_packages)

DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "app.log")
PID_FILE = os.path.join(DATA_DIR, "app.pid")

# Windows pythonw.exe altında sys.stdout ve sys.stderr None gelir.
# Bu durum print veya uvicorn çalıştığında çökmeye neden olur.
# Akışları güvenle data/app.log dosyasına yönlendiriyoruz:
try:
    log_fp = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None or getattr(sys.stdout, 'write', None) is None:
        sys.stdout = log_fp
    if sys.stderr is None or getattr(sys.stderr, 'write', None) is None:
        sys.stderr = log_fp
except Exception:
    pass

def show_error(title, message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, str(message), str(title), 0x10)
    except Exception:
        pass

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(start_port: int = 8000, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port

def wait_and_open_browser(port: int):
    url = f"http://127.0.0.1:{port}"
    for _ in range(30):
        time.sleep(0.5)
        if is_port_in_use(port):
            break
    time.sleep(0.3)
    try:
        webbrowser.open(url)
    except Exception as e:
        try:
            os.system(f"start {url}")
        except Exception:
            print(f"Tarayici acilamadi: {e}", file=sys.stderr)

def cleanup_pid():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass

atexit.register(cleanup_pid)

def main():
    try:
        port = find_free_port(8000)
        
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(f"{os.getpid()}:{port}")
        except Exception:
            pass

        threading.Thread(target=wait_and_open_browser, args=(port,), daemon=True).start()

        import uvicorn
        log_config = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
        if "formatters" in log_config:
            for fmt in log_config["formatters"].values():
                fmt["use_colors"] = False

        uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False, log_config=log_config)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        show_error("Ön Muhasebe Pro Başlatma Hatası",
                   f"Program başlatılırken bir hata oluştu:\\n\\n{e}\\n\\nAyrıntılar: data\\\\app.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    with open(os.path.join(APP_DIR, "run.py"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(run_py_content)

    # 8. kisayol_olustur.vbs (Temiz, bağımsız VBScript kısayol motoru, Windows CRLF)
    vbs_content = """' Özerler Mermer - Masaüstü ve Başlat Menüsü Kısayol Oluşturucu
Option Explicit

Dim ws, fso, desktop, programs, progDir, targetDir
Dim sc1, sc2, sc3, sc4

Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

If WScript.Arguments.Count > 0 Then
    targetDir = WScript.Arguments(0)
Else
    targetDir = fso.GetParentFolderName(WScript.ScriptFullName)
End If

desktop = ws.SpecialFolders("Desktop")
programs = ws.SpecialFolders("Programs")

' 1. Masaüstü Kısayolu
Set sc1 = ws.CreateShortcut(desktop & "\\Özerler Mermer - Ön Muhasebe.lnk")
sc1.TargetPath = "wscript.exe"
sc1.Arguments = Chr(34) & targetDir & "\\Baslat_Sessiz.vbs" & Chr(34)
sc1.WorkingDirectory = targetDir
sc1.IconLocation = targetDir & "\\app.ico,0"
sc1.Description = "Özerler Mermer Ön Muhasebe ve Fatura Takip Programı"
sc1.Save

' 2. Başlat Menüsü Klasörü ve Kısayolları
progDir = programs & "\\Özerler Mermer"
If Not fso.FolderExists(progDir) Then
    fso.CreateFolder(progDir)
End If

Set sc2 = ws.CreateShortcut(progDir & "\\Ön Muhasebe Pro.lnk")
sc2.TargetPath = "wscript.exe"
sc2.Arguments = Chr(34) & targetDir & "\\Baslat_Sessiz.vbs" & Chr(34)
sc2.WorkingDirectory = targetDir
sc2.IconLocation = targetDir & "\\app.ico,0"
sc2.Save

Set sc3 = ws.CreateShortcut(progDir & "\\Sunucuyu Durdur.lnk")
sc3.TargetPath = targetDir & "\\Durdur.bat"
sc3.WorkingDirectory = targetDir
sc3.Save

Set sc4 = ws.CreateShortcut(progDir & "\\Konsollu Başlat (Hata Ayıklama).lnk")
sc4.TargetPath = targetDir & "\\Baslat.bat"
sc4.WorkingDirectory = targetDir
sc4.IconLocation = targetDir & "\\app.ico,0"
sc4.Save
"""
    with open(os.path.join(APP_DIR, "kisayol_olustur.vbs"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(vbs_content)

    # 9. Baslat.bat (Konsollu Başlatıcı, Windows CRLF)
    baslat_bat = """@echo off
chcp 65001 >nul 2>&1
title Özerler Mermer - Ön Muhasebe Pro
cd /d "%~dp0"

echo ============================================================
echo       ÖZERLER MERMER - ÖN MUHASEBE PRO BAŞLATILIYOR
echo ============================================================
echo.
echo Sunucu adresi: http://127.0.0.1:8000
echo Varsayılan web tarayıcınız otomatik olarak açılacaktır...
echo.
echo NOT: Bu konsol penceresini açık bırakınız.
echo Kapatmak için Durdur.bat çalıştırabilir veya pencereyi kapatabilirsiniz.
echo ============================================================
echo.

if not exist "%~dp0python\\python.exe" (
    echo [HATA] Gömülü Python ortamı bulunamadı: %~dp0python\\python.exe
    echo Lütfen arşivdeki tüm dosyaları eksiksiz olarak klasöre çıkarınız.
    pause
    exit /b 1
)

REM Gerekli Visual C++ kütüphanesi eksikse otomatik yükle
if not exist "%SystemRoot%\\System32\\vcruntime140.dll" (
    if exist "%~dp0redist\\VC_redist.x64.exe" (
        echo [BİLGİ] Gerekli sistem bileşeni (Visual C++) eksik, kuruluyor...
        "%~dp0redist\\VC_redist.x64.exe" /passive /norestart
    )
)

"%~dp0python\\python.exe" "%~dp0run.py"

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo [HATA] Program beklenmeyen bir şekilde sonlandı (Kod: %errorlevel%).
    echo Sorun gidermek için Teshis.bat dosyasını çalıştırabilir veya
    echo data\\app.log dosyasını inceleyebilirsiniz.
    echo ============================================================
    pause
)
"""
    with open(os.path.join(APP_DIR, "Baslat.bat"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(baslat_bat)

    # 10. Baslat_Sessiz.vbs (Sessiz / Penceresiz Masaüstü Başlatıcı, Windows CRLF)
    baslat_vbs = """' Özerler Mermer - Ön Muhasebe Pro Sessiz Başlatıcı
Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

currentPath = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = currentPath & "\\python\\pythonw.exe"
runPy = currentPath & "\\run.py"

If Not fso.FileExists(pythonExe) Then
    localAppData = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    If fso.FileExists("C:\\OnMuhasebePro\\python\\pythonw.exe") Then
        currentPath = "C:\\OnMuhasebePro"
        pythonExe = currentPath & "\\python\\pythonw.exe"
        runPy = currentPath & "\\run.py"
    ElseIf fso.FileExists(localAppData & "\\OnMuhasebePro\\python\\pythonw.exe") Then
        currentPath = localAppData & "\\OnMuhasebePro"
        pythonExe = currentPath & "\\python\\pythonw.exe"
        runPy = currentPath & "\\run.py"
    Else
        MsgBox "Program dosyalari bulunamadi!" & vbCrLf & vbCrLf & _
               "Lutfen 'Baslat_Sessiz.vbs' dosyasini klasorunden disari tasimayiniz." & vbCrLf & _
               "Masaustune kisayol olusturmak icin 'Kurulum.bat' veya" & vbCrLf & _
               "'Masaustune_Kisayol_Olustur.bat' dosyasini calistiriniz.", _
               vbCritical, "Özerler Mermer - Ön Muhasebe"
        WScript.Quit 1
    End If
End If

WshShell.CurrentDirectory = currentPath
cmd = Chr(34) & pythonExe & Chr(34) & " " & Chr(34) & runPy & Chr(34)
WshShell.Run cmd, 0, False
"""
    with open(os.path.join(APP_DIR, "Baslat_Sessiz.vbs"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(baslat_vbs)

    # 11. Durdur.bat (Sunucuyu Durdurucu, Windows CRLF)
    durdur_bat = """@echo off
chcp 65001 >nul 2>&1
title Ön Muhasebe Pro - Sunucuyu Durdur
cd /d "%~dp0"

echo Ön Muhasebe Pro sunucusu durduruluyor...
set FOUND=0

REM 1. data\\app.pid dosyasından PID oku ve sonlandır
if exist "data\\app.pid" (
    for /f "tokens=1,2 delims=:" %%a in (data\\app.pid) do (
        if not "%%a"=="" (
            taskkill /F /PID %%a >nul 2>&1
            if %errorlevel% equ 0 set FOUND=1
        )
    )
    del "data\\app.pid" >nul 2>&1
)

REM 2. Port 8000 ve ardışık portları dinleyen processleri kapat
for /L %%p in (8000,1,8015) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%%p" ^| find "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
        set FOUND=1
    )
)

if "%FOUND%"=="1" (
    echo.
    echo [BAŞARILI] Sunucu başarıyla durduruldu.
) else (
    echo.
    echo [BİLGİ] Çalışan aktif bir sunucu bulunamadı veya zaten durdurulmuş.
)

timeout /t 2 >nul
"""
    with open(os.path.join(APP_DIR, "Durdur.bat"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(durdur_bat)

    # 12. Masaustune_Kisayol_Olustur.bat (Windows CRLF)
    kisayol_bat = """@echo off
chcp 65001 >nul 2>&1
title Masaüstü Kısayolu Oluştur
cd /d "%~dp0"

echo Masaüstüne 'Özerler Mermer - Ön Muhasebe' kısayolu ekleniyor...

set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

if exist "%TARGET_DIR%\\kisayol_olustur.vbs" (
    cscript //nologo "%TARGET_DIR%\\kisayol_olustur.vbs" "%TARGET_DIR%"
) else (
    echo [HATA] kisayol_olustur.vbs bulunamadı!
)

if %errorlevel% equ 0 (
    echo.
    echo [BAŞARILI] Kısayol masaüstünüze başarıyla eklendi!
) else (
    echo.
    echo [UYARI] Kısayol oluşturulurken bir sorun oluştu.
)
timeout /t 3 >nul
"""
    with open(os.path.join(APP_DIR, "Masaustune_Kisayol_Olustur.bat"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(kisayol_bat)

    # 13. Teshis.bat (Sorun Giderme ve Sistem Teşhis Aracı, Windows CRLF)
    teshis_bat = """@echo off
chcp 65001 >nul 2>&1
title Ön Muhasebe Pro - Sistem Teşhis ve Test Aracı
cd /d "%~dp0"

echo ============================================================
echo   ÖZERLER MERMER - ÖN MUHASEBE PRO SİSTEM KONTROL VE TEŞHİS
echo ============================================================
echo.
echo Bu araç, sisteminizdeki olası eksiklikleri tespit eder.
echo.

set HATA_VAR=0

echo 1. Dosya bütünlüğü kontrol ediliyor...
if not exist "%~dp0python\\python.exe" (
    echo    [HATA] python\\python.exe bulunamadı!
    echo    SEBEP: Dosyaları ZIP arşivinden çıkarmadan doğrudan ZIP içinde
    echo    çalıştırmış olabilirsiniz. Lütfen ZIP'e sağ tıklayıp "Tümünü Ayıkla" deyiniz.
    set HATA_VAR=1
) else (
    echo    [TAMAM] Python çalışma dosyaları mevcut.
)

echo.
echo 2. Visual C++ çalışma kütüphaneleri kontrol ediliyor...
set VC_EKSİK=0
if not exist "%SystemRoot%\\System32\\vcruntime140.dll" set VC_EKSİK=1
if not exist "%SystemRoot%\\System32\\msvcp140.dll" set VC_EKSİK=1

if "%VC_EKSİK%"=="1" (
    echo    [UYARI] Windows sisteminizde Visual C++ kütüphaneleri eksik görünüyor.
    echo    Bu durum Python'un açılmasını engelleyebilir.
    if exist "%~dp0redist\\VC_redist.x64.exe" (
        echo    Klasör içindeki redist\\VC_redist.x64.exe otomatik kurulabilir.
    )
) else (
    echo    [TAMAM] Visual C++ sistem kütüphaneleri mevcut.
)

echo.
echo 3. Python ve kütüphane çalıştırma testi yapılıyor...
if exist "%~dp0python\\python.exe" (
    "%~dp0python\\python.exe" -c "import sys, sqlite3; print('   [TAMAM] Python ve SQLite calisiyor (Python ' + sys.version.split()[0] + ')')"
    if %errorlevel% neq 0 (
        echo    [HATA] Python başlatılamadı! Hata kodu: %errorlevel%
        echo    Lütfen redist klasöründeki VC_redist.x64.exe dosyasını çalıştırınız.
        set HATA_VAR=1
    ) else (
        "%~dp0python\\python.exe" -c "import fastapi, uvicorn, pydantic; print('   [TAMAM] FastAPI, Uvicorn ve Pydantic yuklu ve hazir.')"
        if %errorlevel% neq 0 (
            echo    [HATA] Muhasebe kütüphaneleri yüklenemedi! Hata kodu: %errorlevel%
            set HATA_VAR=1
        )
    )
)

echo.
echo 4. Veritabanı kontrol ediliyor...
if not exist "%~dp0data\\muhasebe.db" (
    echo    [BİLGİ] data\\muhasebe.db henüz yok, ilk başlatmada otomatik oluşturulacaktır.
) else (
    echo    [TAMAM] data\\muhasebe.db veritabanı mevcut.
)

echo.
echo 5. Port kontrolü (8000)...
netstat -aon 2>nul | find ":8000" | find "LISTENING" >nul
if %errorlevel% equ 0 (
    echo    [BİLGİ] Port 8000 şu anda başka bir program tarafından kullanılıyor.
    echo    (Program otomatik olarak bir sonraki boş portu seçecektir).
) else (
    echo    [TAMAM] Port 8000 boş ve kullanıma hazır.
)

echo.
echo ============================================================
if "%HATA_VAR%"=="0" (
    echo [SONUÇ] TEBRİKLER! Tüm kontroller başarıyla geçti.
    echo Programı çalıştırmak için:
    echo - Sessiz başlatmak için: Baslat_Sessiz.vbs
    echo - Konsollu başlatmak için: Baslat.bat
    echo - Bilgisayara kurmak için: Kurulum.bat
) else (
    echo [SONUÇ] Bazı sorunlar tespit edildi!
    echo Lütfen yukarıdaki [HATA] uyarılarını kontrol ediniz.
    if exist "%~dp0redist\\VC_redist.x64.exe" (
        echo.
        echo İPUCU: Visual C++ hatası alıyorsanız redist\\VC_redist.x64.exe dosyasını kurunuz.
    )
)
echo ============================================================
echo.
pause
"""
    with open(os.path.join(APP_DIR, "Teshis.bat"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(teshis_bat)

    # 14. Kurulum.bat (Yetki hatası vermeyen, VC++ kontrollü, temiz CRLF kurulum sihirbazı)
    kurulum_bat = """@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Özerler Mermer - Ön Muhasebe Kurulumu
cd /d "%~dp0"

echo ============================================================
echo       ÖZERLER MERMER - ÖN MUHASEBE PRO KURULUM SİHİRBAZI
echo ============================================================
echo.
echo Bu sihirbaz programı bilgisayarınıza kuracak
echo ve masaüstünüze kısayol oluşturacaktır.
echo.
echo Kurulum İNTERNET GEREKTİRMEZ (Tamamen Çevrimdışı / Offline).
echo ============================================================
echo.
pause

set "SOURCE_DIR=%~dp0"
if "%SOURCE_DIR:~-1%"=="\\" set "SOURCE_DIR=%SOURCE_DIR:~0,-1%"

REM Gerekli Visual C++ kütüphanesi eksikse otomatik yüklemeyi dene
if not exist "%SystemRoot%\\System32\\vcruntime140.dll" (
    if exist "%SOURCE_DIR%\\redist\\VC_redist.x64.exe" (
        echo.
        echo [BİLGİ] Gerekli sistem kütüphanesi (Microsoft Visual C++) yükleniyor...
        echo Lütfen bekleyiniz...
        "%SOURCE_DIR%\\redist\\VC_redist.x64.exe" /passive /norestart
    )
)

set "TARGET_DIR=C:\\OnMuhasebePro"

REM C:\\ kök dizinine yazma yetkisi var mı test et:
mkdir "C:\\test_onmuhasebe_perm" >nul 2>&1
if %errorlevel% equ 0 (
    rmdir "C:\\test_onmuhasebe_perm" >nul 2>&1
    set "CAN_WRITE_C=1"
) else (
    set "CAN_WRITE_C=0"
)

if "%CAN_WRITE_C%"=="0" (
    echo [BİLGİ] Standart kullanıcı modu algılandı.
    echo Yönetici izni gerekmeden güvenli kurulum için:
    set "TARGET_DIR=%LOCALAPPDATA%\\OnMuhasebePro"
    echo Konum: %LOCALAPPDATA%\\OnMuhasebePro
)

REM Zaten hedef klasörde mi çalıştırılıyor?
if /i "%SOURCE_DIR%"=="%TARGET_DIR%" (
    echo Zaten hedef klasördesiniz. Dosya kopyalama atlanıyor.
    goto MakeShortcut
)

echo.
echo Dosyalar kopyalanıyor: %TARGET_DIR% ...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
xcopy /E /I /Y /Q "%SOURCE_DIR%\\*" "%TARGET_DIR%\\"
if %errorlevel% neq 0 (
    echo [UYARI] Kopyalama tamamlandı (bazı dosyalar atlanmış olabilir).
)

:MakeShortcut
echo.
echo Masaüstü ve Başlat Menüsü kısayolları oluşturuluyor...
if exist "%TARGET_DIR%\\kisayol_olustur.vbs" (
    cscript //nologo "%TARGET_DIR%\\kisayol_olustur.vbs" "%TARGET_DIR%"
) else if exist "%SOURCE_DIR%\\kisayol_olustur.vbs" (
    cscript //nologo "%SOURCE_DIR%\\kisayol_olustur.vbs" "%TARGET_DIR%"
)

echo.
echo ============================================================
echo [BAŞARILI] Kurulum tamamlandı!
echo Program konumu: %TARGET_DIR%
echo Masaüstünüzdeki 'Özerler Mermer - Ön Muhasebe' simgesine
echo tıklayarak hemen kullanabilirsiniz.
echo ============================================================
echo.
set /p START_NOW="Program şimdi başlatılsın mı? (E/H) [Varsayılan: E]: "
if /i "%START_NOW%"=="H" goto End
start "" wscript.exe "%TARGET_DIR%\\Baslat_Sessiz.vbs"

:End
timeout /t 3 >nul
"""
    with open(os.path.join(APP_DIR, "Kurulum.bat"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(kurulum_bat)

    # 15. setup.iss (Inno Setup Scripti, Windows CRLF)
    setup_iss = """#define MyAppName "Özerler Mermer - Ön Muhasebe Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Özerler Mermer San. ve Tic. Ltd. Şti."
#define MyAppExeName "Baslat_Sessiz.vbs"

[Setup]
AppId={{9C52E52F-C639-44F8-B056-1188402D2E65}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\\OnMuhasebePro
DefaultGroupName=Özerler Mermer
OutputDir=..
OutputBaseFilename=OnMuhasebePro_Setup
SetupIconFile=app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "wscript.exe"; Parameters: \"\"\"{app}\\{#MyAppExeName}\"\"\"; WorkingDir: "{app}"; IconFilename: "{app}\\app.ico"
Name: "{group}\\Sunucuyu Durdur"; Filename: "{app}\\Durdur.bat"; WorkingDir: "{app}"
Name: "{group}\\Konsollu Başlat (Hata Ayıklama)"; Filename: "{app}\\Baslat.bat"; WorkingDir: "{app}"; IconFilename: "{app}\\app.ico"
Name: "{group}\\Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "wscript.exe"; Parameters: \"\"\"{app}\\{#MyAppExeName}\"\"\"; WorkingDir: "{app}"; IconFilename: "{app}\\app.ico"; Tasks: desktopicon

[Run]
Filename: "wscript.exe"; Parameters: \"\"\"{app}\\{#MyAppExeName}\"\"\"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
"""
    with open(os.path.join(APP_DIR, "setup.iss"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(setup_iss)

    # 16. BENIOKU.txt (Windows CRLF)
    benioku_txt = """========================================================================
   ÖZERLER MERMER — ÖN MUHASEBE PRO (WINDOWS OFFLINE KURULUM PAKETİ)
========================================================================

Bu paket, programın HERHANGİ BİR WINDOWS BİLGİSAYARDA internet bağlantısı,
Python kurulumu veya harici bir kütüphane gerektirmeksizin %100 ÇEVRİMDIŞI
(OFFLINE) olarak çalışabilmesi için özel olarak hazırlanmıştır.

İçerisinde 64-bit Windows gömülü Python çalışma ortamı, FastAPI sunucusu,
SQLite veritabanı motoru, Microsoft Visual C++ redistributable bileşeni
ve tüm yerel web arayüzü dosyaları dahildir.

------------------------------------------------------------------------
KULLANIM VE KURULUM SEÇENEKLERİ (İstediğinizi Seçebilirsiniz):
------------------------------------------------------------------------

SEÇENEK 1: TEK TIKLA BİLGİSAYARA KURULUM (Önerilen)
---------------------------------------------------
1. "Kurulum.bat" dosyasına çift tıklayın.
2. Program dosyaları otomatik olarak bilgisayarınıza kurulur.
   (Yönetici izni gerektirmez, her Windows bilgisayarda sorunsuz çalışır).
3. Masaüstünüze ve Başlat Menünüze "Özerler Mermer - Ön Muhasebe" kısayolu
   otomatik olarak eklenir.
4. Artık masaüstünüzdeki simgeye çift tıklayarak programı hemen kullanabilirsiniz!

SEÇENEK 2: PORTATİF (TAŞINABİLİR / USB BELLEK) KULLANIM
------------------------------------------------------
Kurulum yapmadan, bu klasörü doğrudan USB bellekte veya istediğiniz bir
klasörde taşıyarak da çalıştırabilirsiniz:
- "Baslat_Sessiz.vbs": Programı arkada sessizce başlatır ve web tarayıcınızı
  (Chrome, Edge vb.) otomatik açar.
- "Baslat.bat": Konsol ekranını görerek başlatmak veya bir hata olup olmadığını
  incelemek isterseniz bunu kullanabilirsiniz.
- "Masaustune_Kisayol_Olustur.bat": Klasörün bulunduğu konuma göre masaüstünüze
  kısayol ekler.

SEÇENEK 3: INNO SETUP İLE .EXE KURULUM DOSYASI DERLEME
-----------------------------------------------------
Klasör içerisindeki "setup.iss" dosyası, Inno Setup 6 ile tek tıkla
"OnMuhasebePro_Setup.exe" kurulum dosyası üretecek şekilde hazır olarak
yapılandırılmıştır.

------------------------------------------------------------------------
PROGRAMI DURDURMAK / KAPATMAK İÇİN:
------------------------------------------------------------------------
Programı tamamen durdurmak isterseniz "Durdur.bat" dosyasına çift tıklamanız
veya Başlat Menüsündeki "Sunucuyu Durdur" kısayolunu kullanmanız yeterlidir.

------------------------------------------------------------------------
BİR SORUN OLURSA (HATA AYIKLAMA VE TEŞHİS):
------------------------------------------------------------------------
1. "Teshis.bat" dosyasına çift tıklayınız. Sisteminizdeki olası eksikleri
   ve neden açılmadığını adım adım test edip ekranda gösterir.
2. "Baslat.bat" dosyasına tıklayarak açılan siyah penceredeki hata mesajını
   okuyabilirsiniz.
3. Bilgisayarınızda "MSVCP140.dll bulunamadı" hatası çıkarsa, "redist"
   klasöründeki "VC_redist.x64.exe" dosyasını kurunuz.
4. Ayrıntılı sistem kayıtları "data\\app.log" dosyasında tutulmaktadır.

------------------------------------------------------------------------
VERİLERİNİZİN YEDEĞİ:
------------------------------------------------------------------------
Tüm cari hesaplarınız, faturalarınız, stoklarınız ve kasa/banka hareketleriniz
"data\\muhasebe.db" dosyası içerisinde güvenle saklanır.
Yedek almak için sadece "data" klasörünü kopyalamanız veya program içerisindeki
"Firma Ayarları -> Veritabanı Yedeği İndir" butonuna tıklamanız yeterlidir.
========================================================================
"""
    with open(os.path.join(APP_DIR, "BENIOKU.txt"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(benioku_txt)

    # 17. ZIP Arşivi Oluştur
    zip_output_path = os.path.join(DIST_DIR, "OnMuhasebePro_Windows_Offline.zip")
    log(f"ZIP arşivi oluşturuluyor: {zip_output_path}...")
    if os.path.exists(zip_output_path):
        os.remove(zip_output_path)

    total_files = 0
    with zipfile.ZipFile(zip_output_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(APP_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DIST_DIR)
                zipf.write(full_path, rel_path)
                total_files += 1

    zip_size_mb = os.path.getsize(zip_output_path) / (1024 * 1024)
    log(f"Tebrikler! Dağıtım paketi başarıyla üretildi: {zip_size_mb:.1f} MB ({total_files} dosya)")
    log(f"Paket Yolu: {zip_output_path}")

def main():
    log("Ön Muhasebe Pro - Windows Offline Paket Derleme Süreci Başlıyor...")
    ensure_cache()
    download_python_embed()
    download_vcredist()
    download_windows_wheels()
    assemble_distribution()
    log("TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    main()
