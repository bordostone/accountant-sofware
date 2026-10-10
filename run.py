# -*- coding: utf-8 -*-
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
