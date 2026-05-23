# CLAUDE.md — VoiceDictation

---

## 0) Git Branch Politikasi

`master`'a push'u sadece repo sahibi `yigitkumral` (Yigit) yapar. Diger
collaborator'lar (su an: `Mertanj`) feature branch acip PR yoluyla katki saglar.

Yigit kendi makinesinde calisirken master'a direkt commit + push edebilir.
Baska bir collaborator olarak calistigini dusunuyorsan: `git checkout -b feature/<konu>`,
push'la, `gh pr create` ile PR ac.

**Commit kurali:** Commit yapmadan **once mutlaka kullanicidan onay al** (kullanicinin global CLAUDE.md kurali).

---

## 0.5) **AGENT'A:** Mac'te Ilk Session Aciliyorsa

Yigit Mac'te yeni bir Claude Code session actiginda **ilk konusmada** bu kontrol listesini hatirlat:

> "Mac'te yeni session. Son Mac dogrulamasi **26 Nisan 2026** (CHANGELOG'da `macOS test paketi`). O tarihten sonra 22-23 Mayis arasi 4 buyuk degisiklik var ve Mac'te dogrulanmadi:
> 1. **Halusinasyon paket 2** (B1-B4 fix) — 23 May
> 2. **Yeni klasor duzeni** (G Drive Records altinda VoiceDictation + RawRecords) — 23 May
> 3. **Lecture WAV dump** (RAM-only ilkesi kaldirildi, WAV RawRecords'a kalici) — 23 May
> 4. **LIVE pass gecici dosyaya** (Drive'a yazilmaz, kayit bitince silinir; gorsel feedback amacli) — 23 May
> 5. **Stop'ta isim dialog** (Windows tkinter + Mac osascript) — 23 May
>
> Sirasiyla test edip Mac-spesifik durumlari dogrulamamiz lazim. TODO.md'de 'Mac'te ilk session' bolumunde tam checklist var."

Bu hatirlatmayi atlamamak kritik — Yigit kendi sormayi unutabilir, agent proaktif onermeli.

---

## 1) Proje Ozeti

VoiceDictation, lokal Whisper modeli ile calisan cross-platform sesli yazim aracidir. Konusmani metne cevirip aktif pencereye yapistirip gonderir.

### Mimari

- **Tek dosya:** `dictation.py` — tum uygulama burasi
- **State Machine (Dictation mode):** LISTENING -> RECORDING -> PROCESSING -> COOLDOWN (mutex ile korunan thread-safe gecisler)
- **Mode (ortogonal eksen):** DICTATION (varsayilan, anlik) ↔ LECTURE (toplanti/ders, ses RawRecords'a WAV olarak diske dokulur)
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

**Akis (23 May 2026 itibariyla):**
1. Kayit baslar — ses sounddevice'tan RAM'e chunk chunk eklenir.
2. **LIVE pass paralel calisir**: cumle-bazli VAD flush ile `tempfile.gettempdir()/voicedictation_live/<ts>_LIVE.md` icine yazilir (Drive'a degil!). Kullanici VS Code'da bu dosyayi otomatik acar, anlik konusmasini izler.
3. Kullanici "⏹ Durdur" der.
4. **Dosya ismi dialog'u** acilir (Windows: tkinter `simpledialog`, macOS: osascript). Default timestamp; kullanici istedigi ismi yazabilir (Cancel/bos -> timestamp kalir).
5. RAM buffer **`RawRecords/<isim>.wav`** olarak diske dokulur (16-bit PCM mono 16kHz, stdlib `wave` modulu).
6. Final transcribe (beam=5, MLX'te `_vad_prefilter` + `condition_on_previous_text=False`).
7. `_finalize_segments`: dusuk-guven dropout (B3) + artifact strip + word correction + filler dedupe (B4).
8. Markdown **`VoiceDictation/<isim>.md`** yazilir, "Kaynak" alani WAV yolunu gosterir.
9. **Gecici LIVE.md silinir** — gorsel feedback amacliydi, arsivlenmez (WAV zaten ses orijinaline geri donus).

**VAD esikleri:**
- `SILENCE_THRESHOLD = 0.008` — dictation kayit no-speech timeout icin

**Beam ayarlari:** dictation `beam=3`, lecture final `beam=5`. RTX GPU'da hiz farki ihmal edilebilir, kalite belirgin iyi.

**Cikti (yeni klasor duzeni, 23 May 2026):**
```
G:\Drive'ım\Records\
├── VoiceDictation\        # MD transkriptler
│   └── <isim>.md
└── RawRecords\            # Islenen ses dosyalari (silinmez, korunur)
    └── <isim>.wav         # Lecture WAV dump
```

**Drive fallback:** G:\ erisilemezse otomatik `~/Desktop/VoiceDictation/{VoiceDictation,RawRecords}/` kullanilir, log'da `[FALLBACK] Drive yok, Desktop'a duser` uyarisi.

**Halusinasyon paket 2 (B1-B4, 23 May 2026):** Bkz. [CHANGELOG.md](CHANGELOG.md). Default davranis: `LECTURE_AGGRESSIVE_CLEANUP=False` -> gercek "evet evet evet" cevaplari korunur; `--aggressive` flag ile opt-in agresif tekrar dedupe.

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

**Cikti (yeni davranis 23 May 2026):**
- MD: `VoiceDictation/<isim>.md` (Drive yoksa Desktop fallback)
- Ses: `shutil.move` ile **`RawRecords/<isim>.<ext>`** olarak tasinir (silinmez, orijinal konumdan kaldirilir). Isim cakisirsa timestamp suffix eklenir.
- `--aggressive` flag opsiyonel: B2 agresif tekrar dedupe (default kapali, gercek "evet evet evet" cevaplari korunur).

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

### Halusinasyon Fix Paketleri

**Paket 1 (22 May 2026, commit `b83e384`):** MLX yoluna Silero VAD on-filtresi + `condition_on_previous_text=False` + `_strip_known_artifacts` segment temizligi. Vaka: `Hakan Hoca Risk Yonetimi 20 Mayis.md` — 70dk "Altyazi M.K." zincirleme tekrar.

**Paket 2 (23 May 2026):** B1-B4 dort kalip icin ek katmanlar. Detay: [CHANGELOG.md](CHANGELOG.md).
- **B1** — Win/faster-whisper `condition_on_previous_text=False` parite + LIVE -> Final pass icin `_strip_known_artifacts` cagrisi quick_transcribe'a tasindi
- **B2** — opt-in agresif tekrar dedupe (`--aggressive` flag, default kapali, gercek "evet evet evet" korunur)
- **B3** — Whisper segment metadata esik filtresi (`avg_logprob`, `no_speech_prob`, `compression_ratio`) `_drop_low_confidence_segments`
- **B4** — filler vocalization regex dedupe (Eee/Hım/Aa 3+ tekrar tekillesir)

Yeni helper'lar: `_drop_low_confidence_segments`, `_dedupe_repeated_segments`, `_finalize_segments`, `_FILLER_RE`.

**Mac dogrulamasi acik:** Paket 1+2 Windows'ta dogrulandi (92sn test, [CHANGELOG.md](CHANGELOG.md)). Mac'te uzaktan mikrofon + uzun sessizlikli senaryo testi yapilmamis — bkz. TODO.md "Mac'te ilk session".

**Ek tavsiye:** iPhone Voice Memo ile paralel kayit hala ideal cozum (mac dahili mic'ten cok daha temiz sinyal). Ardindan `--transcribe`/tray ile cevir; ses RawRecords'a tasinir.

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

*Son Guncelleme: 23 Mayis 2026 — yeni klasor duzeni (G:\Drive Records\{VoiceDictation,RawRecords}), Lecture WAV dump, LIVE pass gecici dosyaya yazar (Drive'a yazilmaz, kayit bitince silinir), halusinasyon paket 2 (B1-B4), stop'ta isim dialog (Windows+Mac), Mac session ilk acilis prompt'u, CHANGELOG.md kuruldu, TODO.md toparlandi.*
