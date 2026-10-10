import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def build():
    print("=========================================================")
    print("   Ön Muhasebe Pro — Bağımsız Paketleme (PyInstaller)")
    print("=========================================================")
    
    # Platform ayrımı (Windows vs Mac/Linux separator)
    sep = ";" if sys.platform.startswith("win") else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=OnMuhasebePro",
        "--onedir",
        "--windowed",
        f"--add-data=static{sep}static",
        f"--add-data=backend{sep}backend",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic",
        "--hidden-import=sqlite3",
        "run_app.py"
    ]

    print("Derleme komutu çalıştırılıyor...")
    print(" ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print("\n=========================================================")
        print("✅ Başarıyla derlendi!")
        print(f"📁 Çıktı Klasörü: {os.path.join(BASE_DIR, 'dist', 'OnMuhasebePro')}")
        print("Bu klasörü doğrudan başka bir bilgisayara kopyalayıp çalıştırabilirsiniz.")
        print("=========================================================\n")
    else:
        print("\n❌ Derleme sırasında bir hata oluştu.")

if __name__ == "__main__":
    build()
