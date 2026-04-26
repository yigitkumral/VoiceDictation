# CLAUDE.md — VoiceDictation

---

## 1) Proje Ozeti

VoiceDictation, lokal Whisper modeli ile calisan cross-platform sesli yazim aracidir. Konusmani metne cevirip aktif pencereye yapistirip gonderir.

### Mimari

- **Tek dosya:** `dictation.py` — tum uygulama burasi
- **State Machine (Dictation mode):** LISTENING -> RECORDING -> PROCESSING -> COOLDOWN (mutex ile korunan thread-safe gecisler)
- **Mode (ortogonal eksen):** DICTATION (varsayilan, anlik) ↔ LECTURE (toplanti/ders, RAM-only)
- **Audio Pipeline:** sounddevice (mikrofon) -> numpy (buffer) -> faster-whisper (STT) -> pyperclip (clipboard) -> pynput (paste+enter)
- **Wake Word:** "Diktasyon" toggle (baslatir + durdurur), genis regex pattern ile Whisper varyasyonlarini yakalar (diktason, dictation, diktatsyon, ...)
- **Hotkey:** F13 (Windows, Logitech G502 sniper button) / Caps Lock x2 (macOS double-tap)

### Platform Destegi

| Platform | GPU | Hotkey | Ses Geri Bildirimi | GUI |
|----------|-----|--------|--------------------|-----|
| Windows | CUDA (otomatik algilama) | F13 (sniper) | winsound WAV | pystray sistem tepsisi ikonu |
| macOS | MLX (Apple Silicon GPU) | Caps Lock x2 (double-tap) | afplay WAV | rumps menu bar ikonu |

### Modlar

#### Dictation Mode (varsayilan)

- F13 / Caps Lock x2 veya "Diktasyon" ile baslar/durur, anlik transcribe (turbo, beam=1)
- Ses tamamen RAM'de — transcribe sonrasi silinir
- Cikti: clipboard'a kopyalanir + aktif pencereye otomatik paste + Enter

#### Lecture Mode (toplanti/ders)

Tray menusunden **"🎙 Toplanti Kaydi Baslat"** ile baslatilir; lecture aktifken F13 dictation hotkey **ignore edilir**, tray ikonu **mor**a doner.

**Onemli ilke: Ses dosyasi DISKE YAZILMAZ — RAM-only.** Tum ses bellekte tutulur, kayit bitince transcribe edilir ve buffer temizlenir. Diskte sadece Markdown transkriptleri kalir.

**Iki seviye transkript:**
- **Canli (LIVE.md):** VAD-bazli cumle akisi — 0.8sn sessizlik = paragraf sonu, max 12sn force-flush, transcribe (turbo, beam=1), MD'ye append; lecture baslarken VS Code'da otomatik acilir, dosya degisimini canli izleyebilirsin
- **Final (.md):** kayit bitince tum ses tek seferde, beam=5 ile yuksek kalite, ayri dosya
- **Footer:** her transkript sonuna `Transkript tamamlandi. Sure: ... • Model: ...` satiri eklenir

**VAD esikleri:**
- `SILENCE_THRESHOLD = 0.008` — dictation kayit no-speech timeout icin
- `LECTURE_LIVE_VAD_THRESHOLD = 0.025` — lecture cumle sonu sessizlik tespiti (mac dahili mic baseline 0.005-0.015 oldugundan ayri tutuldu)

**Cikti:**
```
~/Desktop/VoiceDictation_Lectures/
├── 2026-04-26_15-51-09_LIVE.md   (canli akan, beam=1)
└── 2026-04-26_15-51-09.md         (final, beam=5)
```

#### Dosyadan Transkript

Mevcut bir ses dosyasini (AAC, MP3, WAV, M4A, FLAC, OGG, MP4, **macOS'ta `.qta` Voice Memos lossless dahil**) yuksek kaliteyle MD'ye cevirir.

- **GUI:** Tray menusu → "📁 Ses dosyasini dok..." → dosya secici
  - Windows: tkinter file dialog
  - macOS: **osascript native picker** (tkinter rumps ile main-thread cakismasi yapiyor, kullanilmiyor)
- **CLI (headless, daemon gereksiz):**
  ```bash
  venv/Scripts/python dictation.py --transcribe "FILE.aac"   # Windows
  venv/bin/python dictation.py --transcribe "FILE.qta"        # macOS
  ```

**macOS audio decoder:** mlx_whisper'in dahili `load_audio` ffmpeg subprocess gerektiriyor; ffmpeg yerine **`afconvert` (macOS native)** ile dosya 16kHz mono PCM'e on yuklenir, numpy olarak verilir. ffmpeg dependency'si gerekmiyor.

Cikti: ses dosyasi yaninda `.md` + `~/Desktop/VoiceDictation_Lectures/<isim>.md` (iki kopya).

### Tray Menusu

```
─────────────────────────
 Durum: <state>
─────────────────────────
 🎙 Toplanti Kaydi Baslat / ⏹ Durdur
 📁 Ses dosyasini dok...
─────────────────────────
 🗣️ Anahtar Kelime: Acik/Kapali
 ↺ Sifirla
─────────────────────────
 Cikis
```

### Baslatma

```bash
source venv/bin/activate && python dictation.py
```

### Logging

- `logs/dictation.log` — DEBUG seviyesinden itibaren, gunluk rotate
- Konsol ciktisi INFO seviyesinden itibaren
- Log dizini `.gitignore`'da, git'e girmez

### Teknoloji Stack

- Python 3.10+
- faster-whisper (CTranslate2 tabanli Whisper)
- sounddevice + numpy (audio I/O)
- pynput (global hotkey + keyboard simulation)
- pyperclip (clipboard)
- pystray + Pillow (Windows sistem tepsisi GUI)
- rumps (macOS menu bar GUI)
- logging (dosya + konsol, seviyeli loglama)

### Windows Auto-Start (Bilgisayar Acilisinda Otomatik Baslatma)

Uygulama Windows baslarken otomatik calismali ve her zaman repodaki guncel kodu kullanmali.

**Mekanizma:** Startup klasorune VBScript koyulur, VBScript konsolsuz olarak `start.bat`'i calistirir.

**Dosyalar:**
- `start.bat` — repo kokunde, `venv/Scripts/python.exe dictation.py` calistirir
- `start.vbs` — repo kokunde, `start.bat`'i konsolsuz (gizli pencere) calistirir
- Windows Startup klasoru kisayolu: `shell:startup` → `start.vbs` kisayolu

**Guncelleme Akisi:**
- `dictation.py` degistiginde startup kisayolu guncellenmez — zaten repo'dan calistirilir
- Tek yapilmasi gereken: `git pull` veya kodu duzenlemek
- Bir sonraki bilgisayar acilisinda yeni kod otomatik devreye girer

**Kurulum Adimlari (bir kez yapilir):**
1. `start.bat` ve `start.vbs` dosyalari repo kokunde olusturulur
2. `Win + R` → `shell:startup` → VBScript'e kisayol koyulur
3. Tamamdir — bir daha dokunulmaz

### macOS Auto-Start (Login'de Otomatik Baslatma)

**Mekanizma:** Login Items -> `scripts/VoiceDictation.app` (osacompile uretilen AppleScript .app).
.app `do shell script` ile `venv/bin/python -u dictation.py` calistirir.

> **NEDEN AppleScript .app:** macOS Tahoe Desktop'a TCC kisitlamasi koyuyor.
> - LaunchAgent: mikrofon TCC dialog'u arka planda gosterilemiyor, hang oluyor
> - Login Items + start.sh: TextEdit ile aciliyor, execute olmuyor
> - Login Items + ad-hoc imzali shell-script-app: TCC sessizce reddediyor (`PermissionError`)
> - **Login Items + AppleScript .app:** `Automation` TCC kategorisinde, calisir ✅

**Dosyalar:**
- `scripts/VoiceDictation.app/` — osacompile uretilen .app bundle
  - `Contents/Resources/Scripts/main.scpt` — `do shell script "cd ... && nohup ... &"`
  - `Contents/Info.plist` — `LSUIElement=true` (dock'ta gorunmez)
- `scripts/start.sh` — manuel baslatma icin (Login Items'ta kullanilmaz)

**Guncelleme Akisi:**
- `dictation.py` degistiginde .app guncellenmez — zaten repo'dan calistirilir
- Tek yapilmasi gereken: `git pull` veya kodu duzenlemek
- Bir sonraki login'de yeni kod otomatik devreye girer

**Kurulum Adimlari (bir kez yapilir):**
1. System Settings -> General -> Login Items & Extensions
2. "Open at Login" altinda **+** -> `Cmd+Shift+G` -> `scripts/VoiceDictation.app` yolunu yapistir
3. Ilk acilista **mikrofon** + **otomasyon** izinleri istenir → "Izin Ver"
4. Privacy & Security panellerinde manuel toggle:
   - **Input Monitoring** → `applet` entry'sini AC (Caps Lock hotkey icin)
   - **Accessibility** → `applet` entry'sini AC (Cmd+V + Enter gonderme icin)
5. Dictation'i bir kez yeniden baslat (izin degisikligi icin)
6. Tamamdir — bir daha dokunulmaz

**ZORUNLU 4 IZIN:**
| Izin | Eksikse ne bozulur |
|------|-------------------|
| Mikrofon | Hicbir kayit yapilamaz |
| Otomasyon | .app launcher hata, dictation baslamaz |
| Input Monitoring | Caps Lock algilanmaz (sadece wake word calisir) |
| Accessibility | Metin clipboard'da kalir, paste etmez |

> Stale entry'ler: macOS eski .app denemelerinden TCC'de "VoiceDictation" gibi entry'ler
> birakabilir. **−** butonuyla silinebilir. Aktif olan: `applet`.

**.app yeniden olusturulmasi gerekirse** (osacompile + codesign):
```bash
osacompile -o scripts/VoiceDictation.app <(echo 'do shell script "cd '\''/full/path/to/repo'\'' && nohup venv/bin/python -u dictation.py > /dev/null 2>&1 &"')
# LSUIElement=true ekle Info.plist'e (dock gizleme)
codesign --sign - --force --deep scripts/VoiceDictation.app
```

---

## 2) BMAD-METHOD

Projede [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) (Breakthrough Method for Agile AI-Driven Development) kullanilmaktadir. BMAD, AI destekli yazilim gelistirme surecini uctan uca yoneten bir metodoloji ve agent sistemidir.

### Gelistirme Modeli: AI-Driven Development

- **Planlama** (Brief -> PRD -> Architecture): Insan tarafindan yonetilir
- **Implementation** (epic -> story -> code -> review): AI agentlar tarafindan yurutulur
- Story dongusu: `sprint-planning` -> `create-story` -> `dev-story` -> `code-review`

---

## 3) MCP Tool Map

### filesystem (scope: sadece bu repo)

- Bu MCP yalnizca su dizin icin yetkilidir: `C:\Users\yigit\Desktop\Yazilim\VoiceDictation`
- Kullanim: dosya okuma/yazma, refactor, proje ici arama
- Kural: Repo disina asla yazma/okuma isteme

### context7 (docs dogrulama)

- Kutuphane API/versiyon belirsizse ONCE Context7 ile dogrula
- Once `resolve-library-id` ile kutuphane ID'si al, sonra `query-docs` ile sorgula
- Soru basina en fazla 3 kez cagrilabilir
- Kural: "Hafizadan" API yazma; suphede Context7

### fetch (web erisimi)

- Web sayfalarini okumak icin `mcp__fetch__fetch` kullan
- Built-in WebFetch yerine bu tercih edilir

---

## 4) Tool-Use Protocol

- Dosya degisikligi gerekiyorsa:
  1. filesystem ile ilgili dosyalari ac/oku
  2. plani ozetle (ne degisecek, hangi dosyalar)
  3. uygula
  4. diff/ozet ver
- Dokumantasyon/API suphesi varsa:
  1. context7 ile dogrula
  2. sonra kod yaz

---

## 5) Dil Tercihi

Kullanici ile **Turkce** iletisim kur.

---

*Son Guncelleme: 26 Nisan 2026 (Lecture mode + RAM-only canli transkripsiyon + dosyadan cevirme)*
