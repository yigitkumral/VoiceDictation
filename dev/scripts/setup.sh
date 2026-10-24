#!/bin/bash
cd "$(dirname "$0")/../.." || exit 1
echo "=== VoiceDictation Kurulum (macOS) ==="
echo

# portaudio kontrolu (sounddevice icin gerekli)
if ! brew list portaudio &>/dev/null; then
    echo "[1/3] portaudio kuruluyor (brew install portaudio)..."
    brew install portaudio
else
    echo "[1/3] portaudio zaten kurulu."
fi

if [ ! -d ".local/venv" ]; then
    echo "[2/3] venv olusturuluyor..."
    python3 -m venv .local/venv
else
    echo "[2/3] venv zaten var, atlaniyor."
fi

echo "[3/3] Bagimliliklar kuruluyor (mlx-whisper ve rumps dahil)..."
.local/venv/bin/python -m pip install -r dev/requirements.txt || { echo "HATA: Bagimliliklar kurulamadi."; exit 1; }

echo
echo "Kurulum tamamlandi."
echo "    Veri: .local/data/          Log: .local/logs/"
echo "    Manuel baslatma: ./dev/scripts/start.sh"
echo "    Login'de otomatik baslatma (.app derleme, Login Items, 4 izin): docs/kurulum.md"
echo
