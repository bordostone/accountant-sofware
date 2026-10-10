@echo off
chcp 65001 >nul 2>&1
title Masaüstüne Kısayol Oluştur
cd /d "%~dp0"

echo Masaüstüne ve Başlat Menüsüne kısayollar oluşturuluyor...
cscript //nologo "%~dp0kisayol_olustur.vbs" "%~dp0"

if %errorlevel% equ 0 (
    echo [BAŞARILI] Masaüstünüzde "Özerler Mermer - Ön Muhasebe" kısayolu oluşturuldu.
) else (
    echo [HATA] Kısayol oluşturulamadı.
)
timeout /t 3 >nul
