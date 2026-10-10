#!/usr/bin/env bash
# Ön Muhasebe Pro — macOS Çift Tıkla Başlatıcı

cd "$(dirname "$0")"

echo "========================================================="
echo "   Ön Muhasebe Pro Başlatılıyor..."
echo "========================================================="

# Sanal ortam kontrolü
if [ -d ".venv" ]; then
    ./.venv/bin/python run_app.py
elif command -v python3 &> /dev/null; then
    python3 -m venv .venv
    ./.venv/bin/pip install -r requirements.txt
    ./.venv/bin/python run_app.py
else
    echo "HATA: Python 3 bulunamadı! Lütfen Python 3 kurunuz."
    read -p "Çıkmak için Enter'a basınız..."
fi
