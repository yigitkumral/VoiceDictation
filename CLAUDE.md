# CLAUDE.md — VoiceDictation

---

## 1) Proje Ozeti

VoiceDictation, lokal Whisper modeli ile calisan cross-platform sesli yazim aracidir. Konusmani metne cevirip aktif pencereye yapistirip gonderir.

### Mimari

- **Tek dosya:** `dictation.py` — tum uygulama burasi
- **State Machine:** LISTENING -> RECORDING -> PROCESSING -> COOLDOWN (mutex ile korunan thread-safe gecisler)
- **Audio Pipeline:** sounddevice (mikrofon) -> numpy (buffer) -> faster-whisper (STT) -> pyperclip (clipboard) -> pynput (paste+enter)
- **Wake Word:** "Zugzwang" toggle (baslatir + durdurur), genis regex pattern ile Whisper varyasyonlarini yakalar
- **Hotkey:** F13 (Windows, Logitech G502 sniper button) / Ctrl+Option+R (macOS)

### Platform Destegi

| Platform | GPU | Hotkey | Ses Geri Bildirimi | GUI |
|----------|-----|--------|--------------------|-----|
| Windows | CUDA (otomatik algilama) | F13 (sniper) | winsound WAV | pystray sistem tepsisi ikonu |
| macOS | CPU (fallback) | Ctrl+Option+R | afplay WAV | rumps menu bar ikonu |

### Baslatma

```bash
source venv/bin/activate && python dictation.py
```

### Logging

- `dictation.log` — proje kokunde, DEBUG seviyesinden itibaren
- Konsol ciktisi INFO seviyesinden itibaren
- Log dosyasi `.gitignore`'da, git'e girmez

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

**Mekanizma:** LaunchAgent plist ile login sonrasi `scripts/start.sh` calistirilir.

**Dosyalar:**
- `scripts/start.sh` — `nohup venv/bin/python -u dictation.py` calistirir
- `~/Library/LaunchAgents/com.voicedictation.app.plist` — LaunchAgent tanimi

**Guncelleme Akisi:**
- `dictation.py` degistiginde plist guncellenmez — zaten repo'dan calistirilir
- Tek yapilmasi gereken: `git pull` veya kodu duzenlemek
- Bir sonraki login'de yeni kod otomatik devreye girer

**Kurulum Adimlari (bir kez yapilir):**
1. `~/Library/LaunchAgents/com.voicedictation.app.plist` olusturulur
2. `launchctl load ~/Library/LaunchAgents/com.voicedictation.app.plist`
3. Tamamdir — bir daha dokunulmaz

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

*Son Guncelleme: 19 Mart 2026*
