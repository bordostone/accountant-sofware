@echo off
title Ozerler Mermer - Veritabani Yedekle
cd /d "%~dp0"

echo ============================================================
echo       OZERLER MERMER - VERITABANI YEDEKLEME
echo ============================================================
echo.

if not exist "data\muhasebe.db" (
    echo [HATA] data\muhasebe.db bulunamadi!
    pause
    exit /b 1
)

if not exist "data\yedekler" mkdir "data\yedekler"

powershell -Command "$ts = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'; Copy-Item 'data\muhasebe.db' \"data\yedekler\muhasebe_yedek_$ts.db\"; Write-Host \"[BASARILI] Yedek olusturuldu: data\yedekler\muhasebe_yedek_$ts.db\""

echo.
echo ============================================================
echo Yedekleme islemi tamamlandi.
echo Yedekleriniz data\yedekler klasorunde saklanmaktadir.
echo ============================================================
timeout /t 3 >nul
