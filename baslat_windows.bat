@echo off
if "%~1"=="__RUNNING__" goto :main
cmd /k ""%~f0" __RUNNING__"
exit /b

:main
title Ozerler Mermer - On Muhasebe Pro
cd /d "%~dp0"

echo ============================================================
echo       OZERLER MERMER - ON MUHASEBE PRO
echo ============================================================
echo.
echo Python ortami araniyor, lutfen bekleyiniz...
echo.

if not exist "%~dp0main.py" goto :zip_uyari

where py >nul 2>nul
if %errorlevel% equ 0 goto :py_bulundu

where python >nul 2>nul
if %errorlevel% equ 0 goto :python_bulundu

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe" & goto :exe_bulundu
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & goto :exe_bulundu
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe" & goto :exe_bulundu
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe" & goto :exe_bulundu
if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python39\python.exe" & goto :exe_bulundu
if exist "%ProgramFiles%\Python313\python.exe" set "PY_EXE=%ProgramFiles%\Python313\python.exe" & goto :exe_bulundu
if exist "%ProgramFiles%\Python312\python.exe" set "PY_EXE=%ProgramFiles%\Python312\python.exe" & goto :exe_bulundu
if exist "%ProgramFiles%\Python311\python.exe" set "PY_EXE=%ProgramFiles%\Python311\python.exe" & goto :exe_bulundu
if exist "%ProgramFiles%\Python310\python.exe" set "PY_EXE=%ProgramFiles%\Python310\python.exe" & goto :exe_bulundu
if exist "C:\Python312\python.exe" set "PY_EXE=C:\Python312\python.exe" & goto :exe_bulundu
if exist "C:\Python311\python.exe" set "PY_EXE=C:\Python311\python.exe" & goto :exe_bulundu
if exist "C:\Python310\python.exe" set "PY_EXE=C:\Python310\python.exe" & goto :exe_bulundu

goto :python_yok

:zip_uyari
echo [HATA] ZIP dosyasini klasore cikartmadan calistirdiniz!
echo Lutfen once ZIP dosyasina sag tiklayip "Tumunu Ayikla" secenegini kullaniniz.
echo.
goto :son

:py_bulundu
echo Python Launcher bulundu, baslatiliyor...
py -3 "%~dp0kurulum_ve_baslat.py"
goto :son

:python_bulundu
echo Python bulundu, baslatiliyor...
python "%~dp0kurulum_ve_baslat.py"
goto :son

:exe_bulundu
echo Python bulundu: %PY_EXE%
"%PY_EXE%" "%~dp0kurulum_ve_baslat.py"
goto :son

:python_yok
echo ============================================================
echo [HATA] Bilgisayarinizda calisir durumda Python bulunamadi!
echo ============================================================
echo.
echo Lutfen asagidaki adimlari kontrol ediniz:
echo 1. https://www.python.org/downloads/ adresinden Python 3 kurunuz.
echo    (Kurulum ekraninin en altindaki 'Add python.exe to PATH' kutusunu isaretleyiniz).
echo 2. Veya hic Python kurmadan dogrudan bagimsiz paketi kullanabilirsiniz.
echo.

:son
echo.
echo ============================================================
echo Islem tamamlandi. Pencereyi kapatmak icin herhangi bir tusa basiniz.
echo ============================================================
pause
