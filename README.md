# VoiceDictation

> **Katki / Branch Politikasi**
>
> `master`'a push'u sadece repo sahibi (`yigitkumral`) yapar. Diger
> collaborator'lar feature branch acip Pull Request yoluyla katki saglar:
> `git checkout -b feature/<konu>` -> push -> `gh pr create`. Repo sahibi
> review edip merge eder.

> 🇹🇷 **Bu proje Türkçe konuşma tanıma için özelleştirilmiştir.**
> Whisper modeli `language="tr"` ile çalışır, `INITIAL_PROMPT` Türkçe vocabulary boost'u, halüsinasyon filtreleri (Altyazı M.K., Donama, vb.) Türkçe Whisper çıktılarına göre yazılmıştır. Wake word "Diktasyon"'un regex pattern'ları Whisper'ın **Türkçe** modda ürettiği varyasyonları yakalar (diktasyon, diktason, dictation, diktatsyon...).
> Başka bir dilde kullanmak için kod adaptasyonu gerekir; arayüz, log mesajları, yorumlar Türkçedir.

Lokal Whisper modeli ile calisan cross-platform sesli yazim araci. Konusmani metne cevirip aktif pencereye yapistirip gonderir; ayrica uzun toplanti/ders kayitlari icin RAM-only canli transkripsiyon ve mevcut ses dosyalarini Markdown'a dokme imkani sunar.

## Ozellikler

- **Lokal STT** — Faster-Whisper (CTranslate2) ile internet gerektirmeden sesli yazim
- **Wake Word** — "Diktasyon" diyerek kaydi baslatip durdurabilirsin (degistirilebilir)
- **Hotkey** — F13 (Windows, sniper butonu) / Caps Lock double-tap (macOS) ile toggle
- **Otomatik yapistirma** — Metin clipboard'a kopyalanir, aktif pencereye yapistirip Enter gonderir
- **GPU destegi** — Windows'ta CUDA (RTX serisi), macOS'ta MLX (Apple Silicon GPU)
- **Toplanti/Ders modu** — Uzun kayitlar icin RAM-only canli transkripsiyon, VS Code'da gercek zamanli izleme
- **Dosyadan transkript** — Mevcut AAC/MP3/WAV/M4A dosyalarini yuksek kaliteyle Markdown'a cevirir

## Gereksinimler

- Python 3.10+
- Windows: CUDA Toolkit + cuBLAS (GPU kullanimi icin, opsiyonel)
- macOS: portaudio (`brew install portaudio`)

## Kurulum

### Windows

```bash
git clone https://github.com/yigitkumral/VoiceDictation.git
cd VoiceDictation
setup.bat
```

GPU kullanimi icin CUDA destegi gereklidir. `setup.bat` CUDA kutuphanelerini (cublas, cudnn) otomatik kurar.
CUDA destegi bulunamazsa uygulama otomatik olarak CPU moduna duser.

1. [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) indir ve kur (NVIDIA GPU icin)
2. `setup.bat` calistir — venv, bagimliliklar ve CUDA pip paketleri otomatik kurulur

### macOS

```bash
git clone https://github.com/yigitkumral/VoiceDictation.git
cd VoiceDictation
brew install portaudio
chmod +x setup.sh start.sh
./setup.sh
```

## Hizli Baslangic — Yeni Kullanici Yol Haritasi

Sifirdan baslayan birinin izlemesi gereken adimlar:

1. **Kur** — Yukaridaki adimlarla `setup.bat` (Windows) veya `./setup.sh` (macOS) calistir; venv + bagimliliklar otomatik kurulur
2. **Baslat** — `start.bat` (Windows) / `./start.sh` (macOS); uygulama arka planda calisir, sistem tepsisinde / menu bar'da bir ikon belirir
3. **Ilk dictation denemen** — Hotkey'e bas (F13 / Caps Lock double-tap), bir cumle konus, tekrar bas → metin aktif pencereye yapistirilir + Enter
4. **Wake word'u dene** (opsiyonel) — Tray sag tik → ⚙ Ayarlar → "Anahtar Kelime Dinleme" → **Acik**. Artik "Diktasyon" diyerek de toggle edebilirsin
5. **Bir toplantiyi kaydet** — Tray sag tik → 🎤 Toplanti → "Toplanti Kaydi Baslat"; ikon **mor**a doner, editor'de `LIVE.md` acilir, canli akan transkripti gorursun. "Durdur" deyince yuksek kaliteli final MD uretilir
6. **Mevcut bir ses dosyasini cevir** — Tray menusunden "Ses dosyasini dok..." veya CLI: `venv\Scripts\python dictation.py --transcribe "kayit.aac"`
7. **Auto-start kur** (opsiyonel) — Bilgisayar her acildiginda otomatik baslamasini istiyorsan asagidaki "Auto-Start Kurulumu" bolumune bak

> **Ipucu:** Tray ikon renkleri durumu gosterir — 🔵 mavi: dinleme, 🔴 kirmizi: dictation kaydi, 🟣 mor: lecture (toplanti) kaydi.

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

### Kontroller (Hizli Diktasyon)

| Islem | Windows | macOS |
|-------|---------|-------|
| Kaydi baslat/durdur | F13 (sniper butonu) | Caps Lock double-tap |
| Kaydi baslat/durdur | "Diktasyon" de | "Diktasyon" de |
| Reset (kayit iptal) | F13 1.25sn basili tut | Caps Lock 3x tap (triple-tap) |
| Cikis | Tray/Menu bar -> Cikis | Tray/Menu bar -> Cikis |

### Nasil Calisir (Hizli Diktasyon)

1. **Dinleme modu** — Uygulama arka planda wake word veya hotkey bekler
2. **Kayit** — F13'e bas veya "Diktasyon" de, konusmaya basla
3. **Gonderme** — F13'e tekrar bas veya "Diktasyon" de
4. Metin aktif pencereye yapistirip Enter ile gonderilir

### Tek Nefes Modu

"Diktasyon [mesajin] Diktasyon" seklinde tek nefeste soylersen, mesaj dogrudan gonderilir — kayit moduna gecmeye gerek kalmaz.

### Tray Menusu

Sistem tepsisi ikonuna sag tikla:

```
Durum: <state>
─────────────
🎤 Toplanti  ▶  Toplanti Kaydi Baslat / Durdur
                Ses dosyasini dok...
⚙ Ayarlar    ▶  Anahtar Kelime Dinleme: Acik/Kapali
                Anahtar Kelime: "diktasyon" (degistir...)
─────────────
↺ Sifirla       (cift-tik tray ikonu da resetler)
─────────────
Cikis
```

### Toplanti / Ders Modu (Uzun Kayitlar)

Hizli diktasyondan farkli olarak, **uzun kayitlar** icin tasarlanmistir (toplanti, ders, podcast):

1. Tray sag tik → 🎤 Toplanti → **Toplanti Kaydi Baslat**
2. Tray ikonu mor renge doner; VS Code otomatik acilir, canli MD dosyasi yuklenir
3. VS Code'da **`Ctrl+K V`** ile yan panele Markdown preview ac → konusurken paragraflar canli akar
4. Bitirmek icin: tray → 🎤 Toplanti → **Toplanti Kaydini Durdur**

**Onemli ilke: Ses dosyasi DISKE YAZILMAZ.** Tum ses bellekte tutulur, kayit bitince transcribe edilip RAM temizlenir. Diskte sadece transkript Markdown dosyalari kalir.

**Iki seviye transkript:**
- **Canli (`<tarih>_LIVE.md`):** VAD-bazli cumle akisi (1.5sn sessizlik = paragraf sonu), turbo + beam=1, hizli
- **Final (`<tarih>.md`):** Kayit bitince tum ses, beam=5 ile yuksek kalite, paragraf yapili

**Cikti yapisi:**
```
~/Desktop/VoiceDictation_Lectures/
├── 2026-04-26_18-25-11_LIVE.md    (canli akan)
└── 2026-04-26_18-25-11.md          (final, beam=5)
```

### Dosyadan Transkript

Elindeki bir ses dosyasini (AAC, MP3, WAV, M4A, FLAC, OGG, MP4, **macOS'ta `.qta` Voice Memos lossless** dahil) yuksek kaliteyle Markdown'a cevirir.

**GUI:** Tray sag tik → 🎤 Toplanti → **Ses dosyasini dok...** → dosya secici
- Windows: tkinter dosya dialog'u
- macOS: AppleScript native picker

**CLI (headless, daemon gereksiz):**
```bash
# Windows
venv/Scripts/python dictation.py --transcribe "FILE.aac"

# macOS (qta dahil)
venv/bin/python dictation.py --transcribe "Yeni Kayit.qta"
```

Cikti: ses dosyasi yaninda `.md` + `~/Desktop/VoiceDictation_Lectures/<isim>.md` (iki kopya). Her transkript sonunda `Transkript tamamlandi. Sure: ... • Model: ...` footer'i bulunur.

> **macOS not:** ffmpeg gerekmiyor — `afconvert` (macOS native, dahili) ile dosya 16kHz mono PCM'e on yuklenir.

> **Performans:** 1 saatlik AAC → ~3-5 dakika islem (CUDA + turbo, ~20x realtime; macOS MLX ~40x realtime).

> **macOS Voice Memos dosyalarina ulasma:** Voice Memos sandbox'inda saklar, dogrudan dosya seciciden gorunmez. Bir kayda Voice Memos uygulamasinda **suruklenip Desktop'a birakilir**, sonra picker'dan secilir.

### Anahtar Kelime Degistirme

Default wake word "diktasyon" (Whisper'in genis varyasyon regex'i ile). Degistirmek icin:

1. Tray → ⚙ Ayarlar → **Anahtar Kelime: "..." (degistir...)**
2. Yeni kelime gir, kaydet
3. Yeni kelime hemen aktif olur (basit kelime sinirli case-insensitive eslesme)

**Not:** Default 'diktasyon'a donmek icin dialog'a `diktasyon` yaz.

> Su an wake word degisikligi RAM'de tutulur, daemon restart'ta default'a doner. Disk persist `config.json` ile gelecek.

## Yapilandirma

### dictation.py Sabitleri

Ayarlar dosya icinde:

| Ayar | Varsayilan | Aciklama |
|------|-----------|----------|
| `MODEL_SIZE` | `"turbo"` | Whisper model boyutu (large-v3-turbo) |
| `DEVICE` | Otomatik | `cuda` (CUDA varsa), `mlx` (macOS), `cpu` fallback |
| `SILENCE_THRESHOLD` | `0.008` | Ses algilama esigi |
| `NO_SPEECH_TIMEOUT` | `30.0` | Konusma olmadan zaman asimi (sn) |
| `WAKE_WORD_DEFAULT` | `"diktasyon"` | Default tetikleme kelimesi |
| `LIVE_SILENCE_DURATION` | `0.8` | Lecture mode'da cumle sonu sessizlik (sn) |
| `LIVE_MIN_CHUNK_SECONDS` | `3.0` | Minimum chunk transcribe suresi |
| `LIVE_MAX_CHUNK_SECONDS` | `12.0` | Maksimum chunk (zorla bolme) |
| `LECTURE_LIVE_VAD_THRESHOLD` | `0.025` | Lecture VAD esigi (mic baseline gurultusu yuksekse artir) |

### Environment Variable

| Degisken | Aciklama |
|----------|----------|
| `VOICEDICTATION_EDITOR` | Lecture acilirken kullanilacak editor: `notepad++`, `obsidian`, `subl`, ... veya `none` (sadece clipboard'a kopyala) |

Ornek (PowerShell, kalici):
```powershell
[System.Environment]::SetEnvironmentVariable("VOICEDICTATION_EDITOR", "notepad++", "User")
```

Default sira: ENV var → VS Code (PATH'te varsa) → sistem default → clipboard fallback.

## Auto-Start Kurulumu (Bilgisayar Acilisinda Otomatik Baslat)

Uygulamanin her boot/login'de otomatik calismasini istiyorsan:

### Windows

1. Repo kokunde `start.bat` ve `start.vbs` dosyalari hazir gelir
2. `Win + R` → `shell:startup` → acilan klasore `start.vbs` icin **kisayol** koy
3. Tamam — bir sonraki acilista uygulama konsolsuz olarak baslar

**Guncelleme:** `git pull` veya kod duzenlemesi sonrasi hicbir sey yapma; bir sonraki acilista yeni kod devreye girer (kisayol repo'dan calisir).

### macOS

**Yontem: Login Items + AppleScript .app launcher** (`scripts/VoiceDictation.app`).

> **Not:** Naive Login Items (`start.sh`) ya da LaunchAgent calismiyor cunku macOS Tahoe TCC
> Desktop klasorune erisimi engelliyor. AppleScript .app'i ise `Automation` TCC kategorisinde,
> `do shell script` araciligiyla repo'ya erisebiliyor.

1. **System Settings** ac → **General** → **Login Items & Extensions**
2. Onceki entry varsa (`start.sh` veya LaunchAgent) **−** ile kaldir
3. **Open at Login** bolumunde **+** → `Cmd+Shift+G` → su yolu yapistir:
   ```
   /Users/<kullanici>/Desktop/Yazilim/VoiceDictation/scripts/VoiceDictation.app
   ```
4. **Open** → liste sonuna **VoiceDictation** eklenir
5. Bir sonraki login'de otomatik baslar

### macOS Izinleri (ZORUNLU — Tum 4 Izin Verilmeli)

macOS Tahoe TCC kisitlamalari nedeniyle VoiceDictation **dort ayri izin** gerektirir. Bu
izinler **bir kez** verilir ve sonra tekrar sorulmaz. Eksik izin → bozuk ozellik:

| Izin | Nereden | Hangi ozellik icin |
|------|---------|--------------------|
| **Mikrofon** | Ilk acilista otomatik dialog | Ses kaydi (zorunlu — yoksa hicbir sey calismaz) |
| **Otomasyon** | Ilk acilista otomatik dialog | `do shell script` (.app launcher) |
| **Giris Izleme** (Input Monitoring) | System Settings → Privacy & Security → Input Monitoring | Caps Lock hotkey yakalama (pynput) |
| **Erisilebilirlik** (Accessibility) | System Settings → Privacy & Security → Accessibility | Cmd+V + Enter gonderme (paste-and-send) |

**Eksik izin → ne bozulur:**
- Mikrofon yoksa → kayit yapilamaz (bos transkript)
- Otomasyon yoksa → .app launcher hata verir, dictation hic baslamaz
- Input Monitoring yoksa → Caps Lock x2 algilanmaz, sadece wake word ("Diktasyon") calisir
- Accessibility yoksa → metin clipboard'a kopyalanir ama yapismaz, manuel Cmd+V gerekir

**Kurulum adimlari:**

1. Login Items'a ekle (yukaridaki adimlar)
2. Ilk acilista mikrofon + otomasyon dialog'lari → **Izin Ver**
3. System Settings → Privacy & Security:
   - **Input Monitoring** → liste sonunda `applet` entry'sinin toggle'ini AC
   - **Accessibility** → ayni sekilde `applet` toggle'ini AC
4. Dictation'i yeniden baslat (izin degisikligi icin)

**Birden fazla entry varsa:** macOS bazen eski .app denemelerinden stale entry birakir
(`VoiceDictation`, eski Python yolu, vb.). Bunlari **−** butonu ile silebilirsin. Asil aktif
entry: `applet` (osacompile'in urettigi AppleScript runtime binary).

> Not: Manuel `bash scripts/start.sh` ile baslatildiginda Terminal'in mevcut izinleri
> miras alinir, ekstra izin istenmez. Yukaridaki izinler **otomatik baslatma** (Login Items)
> senaryosu icin sart.

Sonraki acilislarda sessizce baslar.

**Guncelleme:** `git pull` veya kod duzenlemesi sonrasi hicbir sey yapma; bir sonraki login'de
yeni kod devreye girer (.app sadece launcher, dictation.py'yi her zaman repo'dan calistirir).

> Daha onceki LaunchAgent kurulumu varsa kaldirmak icin: `launchctl bootout gui/$(id -u)/com.voicedictation.app && rm -f ~/Library/LaunchAgents/com.voicedictation.app.plist`

## Loglar

- `logs/dictation.log` — DEBUG seviyesinden itibaren, gunluk rotate
- Konsol ciktisi INFO seviyesinden itibaren
- Sorun gidermek icin once bu dosyaya bak

## Teknoloji Stack

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 tabanli Whisper (Windows + Linux)
- [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — Apple Silicon GPU icin Whisper (macOS)
- [sounddevice](https://python-sounddevice.readthedocs.io/) — Mikrofon erisimi
- [pynput](https://pynput.readthedocs.io/) — Global hotkey + klavye simulasyonu
- [pyperclip](https://github.com/asweigart/pyperclip) — Clipboard
- [pystray](https://pystray.readthedocs.io/) + Pillow — Windows sistem tepsisi GUI
- [rumps](https://rumps.readthedocs.io/) — macOS menu bar GUI
- numpy — Audio buffer islemleri

## Lisans

[MIT License](LICENSE) — serbest kullanim. Ticari/akademik/kisisel her amac icin kullanabilir, degistirebilir, dagitabilirsin. Tek kosul: telif notunu yerinde tut.
