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

| Platform | GPU | Hotkey | Ses Geri Bildirimi |
|----------|-----|--------|--------------------|
| Windows | CUDA (RTX 5070) | F13 (sniper) | winsound WAV |
| macOS | CPU (fallback) | Ctrl+Option+R | Henuz yok (TODO) |

### Teknoloji Stack

- Python 3.10+
- faster-whisper (CTranslate2 tabanli Whisper)
- sounddevice + numpy (audio I/O)
- pynput (global hotkey + keyboard simulation)
- pyperclip (clipboard)
- winsound (Windows ses geri bildirimi)

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

*Son Guncelleme: 14 Mart 2026*
