#!/bin/bash
echo "=== Voice Dictation Setup (macOS) ==="
echo

if [ ! -d "venv" ]; then
    echo "[1/3] venv olusturuluyor..."
    python3 -m venv venv
else
    echo "[1/3] venv zaten var, atlaniyor."
fi

echo "[2/3] Bagimliliklar kuruluyor..."
venv/bin/pip install -r requirements.txt

echo
echo "[3/3] Kurulum tamamlandi!"
echo
echo "Calistirmak icin:"
echo "    venv/bin/python dictation.py"
echo
