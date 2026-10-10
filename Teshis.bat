@echo off
if "%~1"=="__RUNNING__" goto :main
cmd /k ""%~f0" __RUNNING__"
exit /b

:main
title Ozerler Mermer - Sistem ve Python Teshis Araci
cd /d "%~dp0"

echo ============================================================
echo       OZERLER MERMER - SISTEM VE PYTHON TESHIS ARACI
echo ============================================================
echo.
echo Bu arac sisteminizdeki Python ortamini test eder.
echo.

set "REPORT=teshis_raporu.txt"
echo --- TESHIS RAPORU --- > "%REPORT%"
echo Tarih: %date% %time% >> "%REPORT%"
echo Dizin: %~dp0 >> "%REPORT%"

echo 1. Python Tespiti...
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo   [OK] Python Launcher (py) mevcut.
    py -3 -c "import sys; print('PY_LAUNCHER:', sys.version)" >> "%REPORT%" 2>&1
) else (
    echo   [-] py launcher bulunamadi.
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo   [OK] PATH uzerinde python mevcut.
    python -c "import sys; print('PATH_PYTHON:', sys.version)" >> "%REPORT%" 2>&1
) else (
    echo   [-] PATH uzerinde python bulunamadi.
)

echo.
echo 2. Kutuphane Kontrolu...
python -c "import fastapi, uvicorn, pydantic; print('FastAPI:', fastapi.__version__)" >> "%REPORT%" 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Kutuphaneler kurulu ve calisiyor.
) else (
    echo   [-] Kutuphaneler henuz kurulmamis. Baslat.bat calistirarak kurabilirsiniz.
)

echo.
echo 3. Port 8000 Kontrolu...
netstat -ano | find "8000" | find "LISTENING" >> "%REPORT%" 2>&1
if %errorlevel% equ 0 (
    echo   [BILGI] Port 8000 su anda kullaniliyor.
) else (
    echo   [OK] Port 8000 bosta ve hazir.
)

echo.
echo ============================================================
echo Teshis tamamlandi. Ayrintili rapor "%REPORT%" dosyasina yazildi.
echo ============================================================
pause
