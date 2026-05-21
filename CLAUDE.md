# CLAUDE.md — VoiceDictation

---

## 0) Git Branch Politikasi

`master`'a push'u sadece repo sahibi `yigitkumral` (Yigit) yapar. Diger
collaborator'lar (su an: `Mertanj`) feature branch acip PR yoluyla katki saglar.

Yigit kendi makinesinde calisirken master'a direkt commit + push edebilir.
Baska bir collaborator olarak calistigini dusunuyorsan: `git checkout -b feature/<konu>`,
push'la, `gh pr create` ile PR ac.

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

- F13 / Caps Lock x2 veya "Diktasyon" ile baslar/durur, anlik transcribe (turbo, beam=3)
- Ses tamamen RAM'de — transcribe sonrasi silinir
- Cikti: clipboard'a kopyalanir + aktif pencereye otomatik paste + Enter

#### Lecture Mode (toplanti/ders)

Tray menusunden **"🎙 Toplanti Kaydi Baslat"** ile baslatilir; lecture aktifken F13 dictation hotkey **ignore edilir**, tray ikonu **mor**a doner.

**Onemli ilke: Ses dosyasi DISKE YAZILMAZ — RAM-only.** Tum ses bellekte tutulur, kayit bitince transcribe edilir ve buffer temizlenir. Diskte sadece Markdown transkriptleri kalir.

**Iki seviye transkript:**
- **Canli (LIVE.md):** VAD-bazli cumle akisi — 0.8sn sessizlik = paragraf sonu, max 12sn force-flush, transcribe (turbo, beam=3), MD'ye append; lecture baslarken VS Code'da otomatik acilir, dosya degisimini canli izleyebilirsin
- **Final (.md):** kayit bitince tum ses tek seferde, beam=5 ile yuksek kalite, ayri dosya
- **Footer:** her transkript sonuna `Transkript tamamlandi. Sure: ... • Model: ...` satiri eklenir

**VAD esikleri:**
- `SILENCE_THRESHOLD = 0.008` — dictation kayit no-speech timeout icin
- `LECTURE_LIVE_VAD_THRESHOLD = 0.025` — lecture cumle sonu sessizlik tespiti (mac dahili mic baseline 0.005-0.015 oldugundan ayri tutuldu)

**Beam ayarlari (16 May 2026):** dictation ve LIVE icin `beam=3` (eskiden `beam=1` idi, ne zaman dustugu net degil; kalite belirgin bozuktu). Final transcribe `beam=5`'te kaldi. Pratikte hiz farki hissedilmiyor (RTX GPU'da decoder yuku encoder yanında ihmal edilebilir), kalite belirgin iyilesti.

**Cikti:**
```
~/Desktop/VoiceDictation_Lectures/
├── 2026-04-26_15-51-09_LIVE.md   (canli akan, beam=3)
└── 2026-04-26_15-51-09.md         (final, beam=5)
```

#### Dosyadan Transkript

Mevcut bir ses dosyasini yuksek kaliteyle (beam=5) MD'ye cevirir.

**Desteklenen formatlar (her iki platform):** AAC, MP3, WAV, M4A, FLAC, OGG, OPUS, WMA, AIFF, CAF, MP4, MOV, MKV, AVI, WEBM, **ve `.qta`** (iPhone Voice Memos QuickTime container — `ftyp qt  `, icerigi sikistirma ayarina gore AAC veya ALAC).

- **GUI:** Tray menusu → "📁 Ses dosyasini dok..." → dosya secici
  - Windows: tkinter file dialog
  - macOS: **osascript native picker** (tkinter rumps ile main-thread cakismasi yapiyor, kullanilmiyor)
- **CLI (headless, daemon gereksiz):**
  ```bash
  venv/Scripts/python dictation.py --transcribe "FILE.aac"   # Windows
  venv/bin/python dictation.py --transcribe "FILE.qta"        # macOS
  ```

**Audio decoder (platform farki):**
- **Windows / faster-whisper:** PyAV (libav) ile container okur — sistem ffmpeg PATH'i gerekmez. AAC/ALAC/MP3/Opus/vs. icerik tipinden bagimsiz dekod eder. Uzanti onemli degil; `.qta` (QuickTime+AAC) dahil tum mobil formatlar **dogrudan calisir** (test edildi: iPhone Voice Memo `Yeni Kayit 24.qta` → 48 kHz stereo AAC → 11.2 dk → 60 sn audio'da 24 segment, Turkce transkript dogru).
- **macOS / mlx-whisper:** mlx_whisper'in dahili `load_audio`'su ffmpeg subprocess gerektiriyor; ffmpeg yerine **`afconvert` (macOS native)** ile dosya 16 kHz mono PCM'e on yuklenir, numpy olarak verilir. ffmpeg dependency'si gerekmiyor.

#### iPhone / Mobil Ses Kayitlari Akisi (Voice Memos, WhatsApp, vs.)

iPhone'da Voice Memos uygulamasi ses kayitlarini iki ayri ayar/uzantida uretir:
- **Compressed (varsayilan):** AAC, 48 kHz, ~64 kbps/ch. Dosya uzantisi `.m4a`. Sticter MP4 container.
- **Lossless (Settings → Voice Memos → Audio Quality → Lossless):** ALAC, 48 kHz. Dosya uzantisi `.qta` (QuickTime Audio). `ftyp qt  ` magic.

iCloud Drive → Google Drive senkronu sonrasi her iki uzanti da PC'ye dusebilir. **Ekstra islem gerekmez:**

1. Dosyayi G-Drive/iCloud'dan local diske kopyala (Drive klasoru disindan calistirmaya gerek yok ama Turkce karakterli path'ler PowerShell ↔ argparse arasinda nadiren sorun cikariyor — emin olmak icin ASCII path).
2. Daemon kapaliyken (tray'den Cikis): `venv\Scripts\python.exe dictation.py --transcribe "C:\path\to\kayit.qta"` (veya `.m4a`).
3. Tray menusundeki "📁 Ses dosyasini dok..." de ayni isi yapar; iki kapi ayni akisi cagiriyor (`transcribe_file_to_markdown` → `_transcribe_audio_path` → beam=5).

> **Daemon calisiyorken `--transcribe` reddedilir** (PID lockfile + ayni GPU'da iki Whisper instance cakisir). Once tray'den Cikis, sonra CLI; bittikten sonra dictation'i geri baslat.

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

### Sessizlik Halusinasyonu Fix'i (22 Mayis 2026)

**Eski problem:** Uzun toplanti/ders kayitlarinda — ozellikle macOS dahili mikrofon + uzaktan konusan konusmaci kombinasyonunda — final pass transkripti "İzlediğiniz için teşekkür ederim", "Altyazı M.K.", "Evet. Evet. Evet.", "İtalyan Folk." gibi YouTube altyazi dataset artifaktlariyla doluyordu. Whisper modeli sessiz veya dusuk sinyalli segmentlerde egitim verisinden bu dolgu cumlelerini halusine eder; bir kez basladiginda kendi ciktisini bir sonraki segment'in prompt'una sokarak zincirleme tekrar eder.

**Vaka:** `Hakan Hoca Risk Yonetimi 20 Mayis.md` — 1sa 35dk lecture, **turbo (mlx)** final pass. Ilk 25dk karisik dolgu (İtalyan Folk, Evet, izlediginiz...), 25-95dk araliginda **70 dakika boyunca "Altyazı M.K." tek satir tekrar**.

**Uygulanan uc fix ([dictation.py](dictation.py)):**

1. **MLX yoluna Silero VAD on-filtresi** ([_vad_prefilter](dictation.py)). `faster-whisper.vad`'in `get_speech_timestamps + SpeechTimestampsMap` helper'lariyla konusma chunk'larini bul, audio'dan sessizligi kirp, MLX'e gonder, sonra segment timestamp'lerini orijinal zamana geri map'le. (iPhone testinde 11dk audio'da %22 sessizlik kirpildi, 0.9sn ek islem.)
2. **`condition_on_previous_text=False`** hem `quick_transcribe` hem de `_transcribe_audio_path` MLX cagrilarinda. Halusinasyon ciksa bile model kendi ciktisini prompt'a sokarak tekrar etmesin — zincirleme tekrar (70dk "Altyazi M.K.") imkansiz hale gelir.
3. **Segment-segment artifact temizleme** (`_strip_known_artifacts`). Final pass sonrasi her segment'i bilinen YouTube kaliplari (`_ARTIFACT_RE` + `_ENGLISH_HALLUC_RE`) ile filtreden gecir, bos kalan segmentleri at. **Onemli:** `_clean_transcription`'in aksine tekrar tespiti YAPMAZ — gercek "evet evet evet" cevaplari korunur, sadece dataset artifakti silinir.

**TO DO — Mac'te gercek lecture testi:** Yeni fix'ler Windows tarafinda (syntax + VAD helper) dogrulandi. Mac'te gercek bir lecture kaydiyla (mikrofon uzakta, uzun sessizlikli) uctan uca test gerekli — beklenti: spam tekrarli artifact yerine bos veya minimal "(sessizlik)" segmentler. Bu testten sonra fix dogrulanir.

**Ek tavsiye:** Kullanim tarafinda iPhone Voice Memo ile paralel kayit hala ideal cozum (mac dahili mic'ten cok daha temiz sinyal). Ardindan `--transcribe`/tray ile cevir.

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

*Son Guncelleme: 22 Mayis 2026 (iPhone Voice Memos akisi netlestirildi + MLX lecture halusinasyon fix'i uygulandi: VAD on-filtre + condition_on_previous_text=False + segment artifact temizligi)*
