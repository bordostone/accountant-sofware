# -*- coding: utf-8 -*-
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
