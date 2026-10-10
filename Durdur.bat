@echo off
title Ozerler Mermer - Sunucuyu Durdur
cd /d "%~dp0"

echo Ozerler Mermer On Muhasebe sunucusu durduruluyor...

set FOUND=0

if exist "data\app.pid" (
    for /f "tokens=1,2 delims=:" %%a in (data\app.pid) do (
        if not "%%a"=="" (
            taskkill /F /PID %%a >nul 2>&1
            if %errorlevel% equ 0 set FOUND=1
        )
    )
    del "data\app.pid" >nul 2>&1
)

for /L %%p in (8000,1,8015) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%%p" ^| find "LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
        set FOUND=1
    )
)

if "%FOUND%"=="1" (
    echo.
    echo [BASARILI] Sunucu basariyla durduruldu.
) else (
    echo.
    echo [BILGI] Calisan aktif sunucu bulunamadi veya zaten durdurulmus.
)

timeout /t 3 >nul
