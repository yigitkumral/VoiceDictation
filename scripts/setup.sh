#!/bin/bash
cd "$(dirname "$0")/.."
echo "=== Voice Dictation Setup (macOS) ==="
echo

# portaudio kontrolu (sounddevice icin gerekli)
if ! brew list portaudio &>/dev/null; then
    echo "[0] portaudio kuruluyor (brew install portaudio)..."
    brew install portaudio
else
    echo "[0] portaudio zaten kurulu."
fi

if [ ! -d "venv" ]; then
    echo "[1/3] venv olusturuluyor..."
    python3 -m venv venv
else
    echo "[1/3] venv zaten var, atlaniyor."
fi

echo "[2/3] Bagimliliklar kuruluyor..."
venv/bin/pip install -r requirements.txt
venv/bin/pip install mlx-whisper

echo
echo "[3/3] Kurulum tamamlandi!"
echo
echo "Calistirmak icin:"
echo "    ./scripts/start.sh"
echo "    # veya"
echo "    venv/bin/python dictation.py"
echo
