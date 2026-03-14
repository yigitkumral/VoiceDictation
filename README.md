# VoiceDictation

Lokal Whisper modeli ile calisan cross-platform sesli yazim araci. Konusmani metne cevirip aktif pencereye yapistirip gonderir.

## Ozellikler

- **Lokal STT** — Faster-Whisper (CTranslate2) ile internet gerektirmeden sesli yazim
- **Wake Word** — "Zugzwang" diyerek kaydi baslatip durdurabilirsin
- **Hotkey** — F13 (Windows, sniper butonu) / Ctrl+Option+R (macOS) ile toggle
- **Otomatik yapistirma** — Metin clipboard'a kopyalanir, aktif pencereye yapistirip Enter gonderir
- **GPU destegi** — Windows'ta CUDA (RTX serisi), macOS'ta CPU fallback

## Gereksinimler

- Python 3.10+
- Windows: CUDA Toolkit + cuBLAS (GPU kullanimi icin)
- macOS: portaudio (`brew install portaudio`)

## Kurulum

### Windows

```bash
git clone <repo-url>
cd VoiceDictation
setup.bat
```

GPU kullanimi icin CUDA destegi gereklidir. `setup.bat` CUDA kutuphanelerini (cublas, cudnn) otomatik kurar.
CUDA destegi bulunamazsa uygulama otomatik olarak CPU moduna duser.

1. [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) indir ve kur (NVIDIA GPU icin)
2. `setup.bat` calistir — venv, bagimliliklar ve CUDA pip paketleri otomatik kurulur

### macOS

```bash
git clone <repo-url>
cd VoiceDictation
brew install portaudio
chmod +x setup.sh start.sh
./setup.sh
```

## Kullanim

### Baslatma

```bash
# Windows
start.bat              # arka planda baslatir
# veya
venv\Scripts\python dictation.py

# macOS
./start.sh             # arka planda baslatir
# veya
venv/bin/python dictation.py
```

### Kontroller

| Islem | Windows | macOS |
|-------|---------|-------|
| Kaydi baslat/durdur | F13 (sniper butonu) | Ctrl+Option+R |
| Kaydi baslat/durdur | "Zugzwang" de | "Zugzwang" de |
| Cikis | Ctrl+Alt+Q | Cmd+Alt+Q |

### Nasil Calisir

1. **Dinleme modu** — Uygulama arka planda wake word veya hotkey bekler
2. **Kayit** — F13'e bas veya "Zugzwang" de, konusmaya basla
3. **Gonderme** — F13'e tekrar bas veya "Zugzwang" de
4. Metin aktif pencereye yapistirip Enter ile gonderilir

### Tek Nefes Modu

"Zugzwang [mesajin] Zugzwang" seklinde tek nefeste soylersen, mesaj dogrudan gonderilir — kayit moduna gecmeye gerek kalmaz.

## Yapilandirma

Ayarlar `dictation.py` icinde sabittir:

| Ayar | Varsayilan | Aciklama |
|------|-----------|----------|
| `MODEL_SIZE` | `"turbo"` | Whisper model boyutu |
| `DEVICE` | Otomatik | `cuda` (CUDA varsa) veya `cpu` (fallback) |
| `SILENCE_THRESHOLD` | `0.008` | Ses algilama esigi |
| `NO_SPEECH_TIMEOUT` | `30.0` | Konusma olmadan zaman asimi (sn) |
| `WAKE_WORD` | `"zugzwang"` | Tetikleme kelimesi |

## Teknoloji Stack

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 tabanli Whisper
- [sounddevice](https://python-sounddevice.readthedocs.io/) — Mikrofon erisimi
- [pynput](https://pynput.readthedocs.io/) — Global hotkey + klavye simulasyonu
- [pyperclip](https://github.com/asweigart/pyperclip) — Clipboard
- numpy — Audio buffer islemleri

## Lisans

Private proje.
