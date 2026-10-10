#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Özerler Mermer - Ön Muhasebe Pro
Windows (Python Kurulu Sistemler İçin) Paketleme ve Betik Oluşturucu
"""

import os
import shutil
import zipfile

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_DIR, "dist_windows")
TARGET_DIR = os.path.join(DIST_DIR, "OnMuhasebe_Windows_Python")
ZIP_FILE = os.path.join(DIST_DIR, "OnMuhasebe_Hizli_Kurulum.zip")

def write_crlf_file(filepath: str, content: str):
    """Dosyayı Windows CRLF ile yazar."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    with open(filepath, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(normalized)

# 1. RUN.PY
RUN_PY_CONTENT = r'''# -*- coding: utf-8 -*-
"""
Ozerler Mermer - On Muhasebe Pro
Windows Calisma ve Masaustu Penceresi Baslatici
"""
import os
import sys
import time
import socket
import atexit
import copy
import threading
import subprocess
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Sanal ortam veya yerel paket dizinleri
for p in [
    os.path.join(ROOT_DIR, ".venv", "Lib", "site-packages"),
    os.path.join(ROOT_DIR, "python", "Lib", "site-packages"),
]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "app.log")
PID_FILE = os.path.join(DATA_DIR, "app.pid")

# Windows pythonw.exe altinda sys.stdout ve sys.stderr None olabilir.
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
        print(f"[{title}] {message}", file=sys.stderr)

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(start_port: int = 8000, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return start_port

def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False

def find_desktop_browser():
    """Windows Edge veya Chrome calistirilabilir dosyasini bulur."""
    candidates = []
    
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    local_app_data = os.environ.get("LocalAppData", os.path.expanduser(r"~\AppData\Local"))
    
    # 1. Edge (Windows 10/11'de yerlesiktir)
    candidates.append(os.path.join(prog_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"))
    candidates.append(os.path.join(prog_files, "Microsoft", "Edge", "Application", "msedge.exe"))
    candidates.append(os.path.join(local_app_data, "Microsoft", "Edge", "Application", "msedge.exe"))
    
    # 2. Chrome
    candidates.append(os.path.join(prog_files, "Google", "Chrome", "Application", "chrome.exe"))
    candidates.append(os.path.join(prog_files_x86, "Google", "Chrome", "Application", "chrome.exe"))
    candidates.append(os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"))
    
    for path in candidates:
        if os.path.isfile(path):
            return path
            
    if sys.platform == "darwin":
        mac_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.isfile(mac_chrome):
            return mac_chrome
            
    return None

def open_desktop_window_only(url: str):
    """Masaustu penceresini acar fakat sureci beklemez (var olan oturum icin)."""
    browser_exe = find_desktop_browser()
    if browser_exe:
        profile_dir = os.path.join(DATA_DIR, ".desktop_profile")
        os.makedirs(profile_dir, exist_ok=True)
        cmd = [
            browser_exe,
            f"--app={url}",
            f"--user-data-dir={profile_dir}",
            "--window-size=1400,900",
            "--app-id=OzerlerOnMuhasebe"
        ]
        try:
            subprocess.Popen(cmd)
            return
        except Exception:
            pass
    try:
        webbrowser.open(url)
    except Exception:
        pass

def wait_and_open_desktop_window(port: int):
    """Sunucunun baslamasini bekler ve bagimsiz masaustu penceresi olarak acar."""
    url = f"http://127.0.0.1:{port}"
    for _ in range(40):
        time.sleep(0.3)
        if is_port_in_use(port):
            break
    time.sleep(0.4)
    
    browser_exe = find_desktop_browser()
    if browser_exe:
        profile_dir = os.path.join(DATA_DIR, ".desktop_profile")
        os.makedirs(profile_dir, exist_ok=True)
        cmd = [
            browser_exe,
            f"--app={url}",
            f"--user-data-dir={profile_dir}",
            "--window-size=1400,900",
            "--app-id=OzerlerOnMuhasebe"
        ]
        try:
            proc = subprocess.Popen(cmd)
            # Kullanici pencereyi kapattiginda sunucu da otomatik durdurulur
            proc.wait()
            cleanup_pid()
            os._exit(0)
        except Exception as e:
            print(f"Masaustu pencere hatasi: {e}", file=sys.stderr)
            try:
                webbrowser.open(url)
            except Exception:
                pass
    else:
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
        # 1. Onceden calisan aktif bir oturum var mi kontrol et
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if ":" in content:
                    old_pid_s, old_port_s = content.split(":", 1)
                    old_pid = int(old_pid_s)
                    old_port = int(old_port_s)
                    if is_pid_running(old_pid) and is_port_in_use(old_port):
                        open_desktop_window_only(f"http://127.0.0.1:{old_port}")
                        sys.exit(0)
            except Exception:
                pass

        port = find_free_port(8000)
        
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(f"{os.getpid()}:{port}")
        except Exception:
            pass

        threading.Thread(target=wait_and_open_desktop_window, args=(port,), daemon=True).start()

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
        show_error("On Muhasebe Pro Baslatma Hatasi",
                   f"Program baslatilirken bir hata olustu:\n\n{e}\n\nAyrintilar: data\\app.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

# 2. KURULUM_VE_BASLAT.PY
KURULUM_VE_BASLAT_PY_CONTENT = r'''# -*- coding: utf-8 -*-
"""
Ozerler Mermer - On Muhasebe Pro
Windows Akilli Kurulum ve Baslatici
"""

import os
import sys
import subprocess
import time
import socket
import webbrowser
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

REQUIRED_PACKAGES = [
    ("fastapi", "fastapi>=0.109.0"),
    ("uvicorn", "uvicorn>=0.27.0"),
    ("pydantic", "pydantic>=2.6.0"),
    ("multipart", "python-multipart>=0.0.9")
]

def print_header():
    print("=" * 60)
    print("      OZERLER MERMER - ON MUHASEBE PRO")
    print("       Akilli Kurulum ve Baslatici")
    print("=" * 60)
    print(f"Python Konumu : {sys.executable}")
    print(f"Python Surumu : {sys.version.split()[0]}")
    print(f"Program Dizini: {BASE_DIR}")
    print("=" * 60)
    print()

def check_and_install_dependencies():
    missing = []
    for mod_name, pkg_req in REQUIRED_PACKAGES:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_req)

    if not missing:
        print("[OK] Tum gerekli kutuphaneler kurulu ve hazir.")
        return True

    print(f"[*] Eksik kutuphaneler tespit edildi ({len(missing)} adet).")
    print("    Otomatik olarak yukleniyor, lutfen bekleyiniz...")
    print(f"    Yuklenecek paketler: {', '.join(missing)}")
    print()

    # 1. Standart pip install dene
    cmd = [sys.executable, "-m", "pip", "install"] + missing
    try:
        ret = subprocess.call(cmd)
        if ret == 0:
            print("[OK] Kutuphaneler basariyla yuklendi!")
            return True
    except Exception as e:
        print(f"[!] pip standart kurulum hatasi: {e}")

    # 2. Eger izin hatasi olduysa --user ile dene
    print("[*] '--user' parametresi ile tekrar deneniyor...")
    cmd_user = [sys.executable, "-m", "pip", "install", "--user"] + missing
    try:
        ret = subprocess.call(cmd_user)
        if ret == 0:
            print("[OK] Kutuphaneler basariyla yuklendi (--user)!")
            return True
    except Exception as e:
        print(f"[!] pip --user kurulum hatasi: {e}")

    print()
    print("[HATA] Kutuphaneler otomatik yuklenemedi!")
    print("Lutfen internet baglantinizi kontrol ediniz veya su komutu calistiriniz:")
    print(f"{sys.executable} -m pip install -r requirements.txt")
    return False

def create_desktop_shortcut():
    """Windows Script Host kullanarak masaustune ve baslat menusune sessiz calisan kisayol olusturur."""
    try:
        kisayol_vbs = os.path.join(BASE_DIR, "kisayol_olustur.vbs")
        if os.path.exists(kisayol_vbs):
            subprocess.call(["cscript", "//nologo", kisayol_vbs, BASE_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[OK] Masaustune 'Ozerler Mermer - On Muhasebe' kisayolu eklendi.")
            return

        user_profile = os.environ.get("USERPROFILE", "")
        desktop = os.path.join(user_profile, "Desktop")
        if not os.path.exists(desktop):
            onedrive_desktop = os.path.join(user_profile, "OneDrive", "Masaüstü")
            if os.path.exists(onedrive_desktop):
                desktop = onedrive_desktop
            else:
                onedrive_desktop_en = os.path.join(user_profile, "OneDrive", "Desktop")
                if os.path.exists(onedrive_desktop_en):
                    desktop = onedrive_desktop_en

        if not os.path.exists(desktop):
            return

        shortcut_path = os.path.join(desktop, "Özerler Mermer - Ön Muhasebe.lnk")
        ico_path = os.path.join(BASE_DIR, "app.ico")
        target_vbs = os.path.join(BASE_DIR, "Baslat_Sessiz.vbs")

        vbs_script = (
            'Set ws = CreateObject("WScript.Shell")\n'
            f'Set sc = ws.CreateShortcut("{shortcut_path}")\n'
            'sc.TargetPath = "wscript.exe"\n'
            f'sc.Arguments = Chr(34) & "{target_vbs}" & Chr(34)\n'
            f'sc.WorkingDirectory = "{BASE_DIR}"\n'
            'sc.Description = "Ozerler Mermer On Muhasebe Pro"\n'
            f'If CreateObject("Scripting.FileSystemObject").FileExists("{ico_path}") Then\n'
            f'    sc.IconLocation = "{ico_path},0"\n'
            'End If\n'
            'sc.Save\n'
        )
        vbs_file = os.path.join(BASE_DIR, "_temp_shortcut.vbs")
        with open(vbs_file, "w", encoding="utf-8") as f:
            f.write(vbs_script)
        
        subprocess.call(["cscript", "//nologo", vbs_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(vbs_file):
            os.remove(vbs_file)
        print("[OK] Masaustune 'Ozerler Mermer - On Muhasebe' kisayolu eklendi.")
    except Exception:
        pass

def start_server():
    print()
    print("=" * 60)
    print("Sunucu baslatiliyor...")
    print("=" * 60)
    
    try:
        import run
        run.main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print()
        print("=" * 60)
        print(f"[HATA] Sunucu baslatilamadi: {e}")
        print("Ayrintilar icin data/app.log dosyasini inceleyiniz.")
        print("=" * 60)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Program baslatilamadi:\n\n{e}\n\nAyrintilar: data/app.log", "On Muhasebe Hata", 0x10)
        except Exception:
            pass

def main():
    print_header()
    
    print("[1/3] Kutuphane kontrolu yapiliyor...")
    success = check_and_install_dependencies()
    if not success:
        print()
        input("Cikmak icin Enter tusuna basiniz...")
        sys.exit(1)
        
    print()
    print("[2/3] Masaustu kisayolu kontrol ediliyor...")
    create_desktop_shortcut()

    print()
    print("[3/3] On Muhasebe Pro calistiriliyor...")
    start_server()

if __name__ == "__main__":
    main()
'''

# 3. BASLAT.BAT & KURULUM.BAT (Kapanmayan Guvenli Baslatici - Parantezsiz Label Mimarisi)
BAT_CONTENT = r'''@echo off
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
'''

# 4. BASLAT_SESSIZ.VBS (Sıfır Konsol, Sessiz Masaüstü Başlatıcı)
BASLAT_SESSIZ_VBS_CONTENT = r'''' Ozerler Mermer - On Muhasebe Pro Sessiz Masaustu Baslatici
Option Explicit

Dim fso, WshShell, currentPath, runPy, pywExe

Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

currentPath = fso.GetParentFolderName(WScript.ScriptFullName)
runPy = currentPath & "\run.py"
WshShell.CurrentDirectory = currentPath

' 1. Yerel pythonw veya sistem pythonw kontrolu
Dim candidates, p, userProf, progFiles, progFiles86, localApp
userProf = WshShell.ExpandEnvironmentStrings("%USERPROFILE%")
localApp = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
progFiles = WshShell.ExpandEnvironmentStrings("%ProgramFiles%")
progFiles86 = WshShell.ExpandEnvironmentStrings("%ProgramFiles(x86)%")

candidates = Array(_
    currentPath & "\.venv\Scripts\pythonw.exe",_
    currentPath & "\python\pythonw.exe",_
    localApp & "\Programs\Python\Python313\pythonw.exe",_
    localApp & "\Programs\Python\Python312\pythonw.exe",_
    localApp & "\Programs\Python\Python311\pythonw.exe",_
    localApp & "\Programs\Python\Python310\pythonw.exe",_
    localApp & "\Programs\Python\Python39\pythonw.exe",_
    progFiles & "\Python313\pythonw.exe",_
    progFiles & "\Python312\pythonw.exe",_
    progFiles & "\Python311\pythonw.exe",_
    progFiles & "\Python310\pythonw.exe",_
    "C:\Python312\pythonw.exe",_
    "C:\Python311\pythonw.exe",_
    "C:\Python310\pythonw.exe"_
)

pywExe = ""
For Each p In candidates
    If fso.FileExists(p) Then
        pywExe = p
        Exit For
    End If
Next

If pywExe <> "" Then
    ' pythonw ile tamamen sessiz (sifir konsol penceresi) baslat
    WshShell.Run Chr(34) & pywExe & Chr(34) & " " & Chr(34) & runPy & Chr(34), 0, False
Else
    ' Pythonw yolu bulunamadiysa, pyw/pythonw komutunu dene veya Baslat.bat'a yonlendir
    On Error Resume Next
    Dim exitCode
    exitCode = WshShell.Run("pyw -3 " & Chr(34) & runPy & Chr(34), 0, False)
    If Err.Number <> 0 Then
        Err.Clear
        exitCode = WshShell.Run("pythonw " & Chr(34) & runPy & Chr(34), 0, False)
        If Err.Number <> 0 Then
            WshShell.Run Chr(34) & currentPath & "\Baslat.bat" & Chr(34), 1, False
        End If
    End If
    On Error GoTo 0
End If
'''

# 5. KISAYOL_OLUSTUR.VBS
KISAYOL_OLUSTUR_VBS_CONTENT = r'''' Özerler Mermer - Masaüstü ve Başlat Menüsü Kısayol Oluşturucu
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
Set sc1 = ws.CreateShortcut(desktop & "\Özerler Mermer - Ön Muhasebe.lnk")
sc1.TargetPath = "wscript.exe"
sc1.Arguments = Chr(34) & targetDir & "\Baslat_Sessiz.vbs" & Chr(34)
sc1.WorkingDirectory = targetDir
sc1.IconLocation = targetDir & "\app.ico,0"
sc1.Description = "Özerler Mermer Ön Muhasebe ve Fatura Takip Programı"
sc1.Save

' 2. Başlat Menüsü Klasörü ve Kısayolları
progDir = programs & "\Özerler Mermer"
If Not fso.FolderExists(progDir) Then
    fso.CreateFolder(progDir)
End If

Set sc2 = ws.CreateShortcut(progDir & "\Ön Muhasebe Pro.lnk")
sc2.TargetPath = "wscript.exe"
sc2.Arguments = Chr(34) & targetDir & "\Baslat_Sessiz.vbs" & Chr(34)
sc2.WorkingDirectory = targetDir
sc2.IconLocation = targetDir & "\app.ico,0"
sc2.Save

Set sc3 = ws.CreateShortcut(progDir & "\Sunucuyu Durdur.lnk")
sc3.TargetPath = targetDir & "\Durdur.bat"
sc3.WorkingDirectory = targetDir
sc3.Save

Set sc4 = ws.CreateShortcut(progDir & "\Konsollu Başlat (Hata Ayıklama).lnk")
sc4.TargetPath = targetDir & "\Baslat.bat"
sc4.WorkingDirectory = targetDir
sc4.IconLocation = targetDir & "\app.ico,0"
sc4.Save
'''

# 6. MASAUSTUNE_KISAYOL_OLUSTUR.BAT
MASAUSTUNE_KISAYOL_BAT_CONTENT = r'''@echo off
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
'''

# 7. DURDUR.BAT
DURDUR_BAT_CONTENT = r'''@echo off
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
'''

# 8. YEDEKLE.BAT
YEDEKLE_BAT_CONTENT = r'''@echo off
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
'''

# 9. TESHIS.BAT
TESHIS_BAT_CONTENT = r'''@echo off
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
'''

# 10. BENIOKU.TXT
BENIOKU_TXT_CONTENT = r'''============================================================
       ÖZERLER MERMER — ÖN MUHASEBE VE FATURA TAKİP
              Masaüstü Uygulaması (Windows)
============================================================

Bu paket, Ön Muhasebe Pro programını bilgisayarınızda yerel ve bağımsız
bir Masaüstü Uygulaması (Desktop App) olarak çalıştırmanızı sağlar.

------------------------------------------------------------
1. İLK KURULUM VE BAŞLATMA:
------------------------------------------------------------
1. İndirdiğiniz ZIP dosyasını bir klasöre çıkartınız (Örn: C:\OnMuhasebe).
2. "Kurulum.bat" (veya "Baslat.bat") dosyasına çift tıklayınız.
3. Program otomatik olarak:
   - Gerekli kütüphaneleri kontrol edip yükler.
   - Masaüstünüze "Özerler Mermer - Ön Muhasebe" simgesini ekler.
   - Programı bağımsız bir MASAÜSTÜ PENCERESİ olarak açar.

------------------------------------------------------------
2. MASAÜSTÜNDEN ÇALIŞTIRMA (GÜNLÜK KULLANIM):
------------------------------------------------------------
- Kurulumdan sonra konsol veya komut satırıyla işiniz yoktur!
- Masaüstünüzdeki "Özerler Mermer - Ön Muhasebe" simgesine çift tıklayarak
  programı doğrudan, arka planda sessizce başlatabilirsiniz.
- Program web tarayıcısı sekmeleri veya adres çubukları olmadan,
  tamamen bağımsız ve çerçevesiz bir Masaüstü Programı olarak açılır.

------------------------------------------------------------
3. PROGRAMI KAPATMA:
------------------------------------------------------------
- Program penceresinin sağ üst köşesindeki "X" (kapat) butonuna bastığınızda
  veya programın sol altındaki / üst çubuğundaki "Programı Kapat / Çıkış"
  butonuna tıkladığınızda tüm işlemler güvenle durdurulur ve pencere kapanır.
- Dilerseniz "Durdur.bat" dosyasına çift tıklayarak da sunucuyu durdurabilirsiniz.

------------------------------------------------------------
4. YEDEKLEME VE VERİ GÜVENLİĞİ:
------------------------------------------------------------
- "Yedekle.bat" dosyasına tıklayarak veritabanınızın tarih/saat damgalı
  yedeğini "data\yedekler" klasörüne alabilirsiniz.
- Ayrıca program içerisinden "Firma & Ayarlar" menüsünden dilediğiniz zaman
  tek tıkla yedek indirebilir veya yedek geri yükleyebilirsiniz.

============================================================
Özerler Mermer San. ve Tic. Ltd. Şti.
============================================================
'''

# 11. REQUIREMENTS.TXT
REQUIREMENTS_CONTENT = '''fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.6.0
python-multipart>=0.0.9
'''

def copy_folder_clean(src, dst):
    """Klasörü __pycache__ ve .DS_Store hariç kopyalar."""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.venv', '.git', '.idea', '.vscode')]
        rel_path = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel_path) if rel_path != '.' else dst
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            if f in ('.DS_Store', 'Thumbs.db', 'app.log', 'app.pid'):
                continue
            if f.endswith('.pyc') or f.endswith('.pyo'):
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))

def main():
    print("=" * 60)
    print("Ön Muhasebe Pro - Python Kurulu Windows Paketi Hazırlanıyor...")
    print("=" * 60)

    # Hedef klasörü hazırla
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR, exist_ok=True)

    # 1. Backend klasörünü kopyala
    print("-> backend klasörü kopyalanıyor...")
    copy_folder_clean(os.path.join(PROJECT_DIR, "backend"), os.path.join(TARGET_DIR, "backend"))

    # 2. Static klasörünü kopyala
    print("-> static klasörü kopyalanıyor...")
    copy_folder_clean(os.path.join(PROJECT_DIR, "static"), os.path.join(TARGET_DIR, "static"))

    # 3. Data klasörünü ve temiz muhasebe.db'yi kopyala
    print("-> data klasörü ve veritabanı kopyalanıyor...")
    target_data = os.path.join(TARGET_DIR, "data")
    os.makedirs(target_data, exist_ok=True)
    source_db = os.path.join(PROJECT_DIR, "data", "muhasebe.db")
    if os.path.exists(source_db):
        shutil.copy2(source_db, os.path.join(target_data, "muhasebe.db"))

    # 4. Ana Python ve kaynak dosyalarını kopyala / yaz
    print("-> main.py kopyalanıyor...")
    shutil.copy2(os.path.join(PROJECT_DIR, "main.py"), os.path.join(TARGET_DIR, "main.py"))

    print("-> app.ico kopyalanıyor...")
    source_ico = os.path.join(PROJECT_DIR, "app.ico")
    shutil.copy2(source_ico, os.path.join(TARGET_DIR, "app.ico"))

    # 5. CRLF ile Windows betiklerini yaz
    print("-> Windows betikleri (CRLF formatında) oluşturuluyor...")
    write_crlf_file(os.path.join(TARGET_DIR, "run.py"), RUN_PY_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "kurulum_ve_baslat.py"), KURULUM_VE_BASLAT_PY_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "requirements.txt"), REQUIREMENTS_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Baslat.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Kurulum.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Calistir.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Baslat_Sessiz.vbs"), BASLAT_SESSIZ_VBS_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "kisayol_olustur.vbs"), KISAYOL_OLUSTUR_VBS_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Masaustune_Kisayol_Olustur.bat"), MASAUSTUNE_KISAYOL_BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Durdur.bat"), DURDUR_BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Yedekle.bat"), YEDEKLE_BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "Teshis.bat"), TESHIS_BAT_CONTENT)
    write_crlf_file(os.path.join(TARGET_DIR, "BENIOKU.txt"), BENIOKU_TXT_CONTENT)

    # 6. Kök dizindeki Windows başlatıcılarını da güncelle
    print("-> Kök dizindeki Windows başlatıcıları güncelleniyor...")
    write_crlf_file(os.path.join(PROJECT_DIR, "run.py"), RUN_PY_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "kurulum_ve_baslat.py"), KURULUM_VE_BASLAT_PY_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Baslat.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Kurulum.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Calistir.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "baslat_windows.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "kurulum_windows.bat"), BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Baslat_Sessiz.vbs"), BASLAT_SESSIZ_VBS_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "kisayol_olustur.vbs"), KISAYOL_OLUSTUR_VBS_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Masaustune_Kisayol_Olustur.bat"), MASAUSTUNE_KISAYOL_BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Durdur.bat"), DURDUR_BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Yedekle.bat"), YEDEKLE_BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "Teshis.bat"), TESHIS_BAT_CONTENT)
    write_crlf_file(os.path.join(PROJECT_DIR, "BENIOKU_WINDOWS.txt"), BENIOKU_TXT_CONTENT)

    # 7. ZIP Paketini Oluştur
    print("-> ZIP arşivi sıkıştırılıyor...")
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)
    
    with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(TARGET_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, TARGET_DIR)
                arcname = os.path.join("OnMuhasebe_Hizli_Kurulum", rel_path)
                zipf.write(full_path, arcname)

    size_mb = os.path.getsize(ZIP_FILE) / (1024 * 1024)
    print("=" * 60)
    print(f"BAŞARILI! Paket hazırlandı:")
    print(f"Klasör : {TARGET_DIR}")
    print(f"ZIP    : {ZIP_FILE} ({size_mb:.2f} MB)")
    print("=" * 60)

if __name__ == "__main__":
    main()
