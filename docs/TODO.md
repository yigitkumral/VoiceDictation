# TODO — VoiceDictation

> **Not:** Tamamlanmis is kayitlari [CHANGELOG.md](CHANGELOG.md) altinda. Bu dosya sadece **acik** islerdir.

---

## Onemli: Mac'te ilk session

**Agent talimatı:** Yigit Mac'te yeni bir Claude Code session actiginda, repo'yu `git pull` ile cektikten sonra **derhal** Mac-spesifik testleri calistirmasini onermeli.

Mac'in son dokunulma tarihi: **26 Nisan 2026** (CHANGELOG'da macOS test paketi). 22-23 Mayis fix'leri (B1-B4 halusinasyon + yeni klasor duzeni + LIVE gecici + stop dialog) Windows'ta dogrulandi, **Mac'te dogrulanmadi**.

Mac'te ilk session acildiginda yapilmasi gerekenler:

- [ ] `git pull` sonrasi `venv` aktif, `python -m py_compile dictation.py` ile syntax kontrolu
- [ ] Daemon'i baslat: `scripts/VoiceDictation.app` (Login Items) veya manuel `venv/bin/python dictation.py`
- [ ] **Sessizlik halusinasyon paket 2 (B1-B4) Mac dogrulamasi**:
  - 2-3 dk lecture kaydet (uzaktan mikrofon, kasitli sessizlikli) -> Final.md'de "Altyazi M.K." benzeri spam YOK
  - "Eee Eee Eee" filler test -> tekillesti mi
  - "Evet evet evet katiliyorum" -> tek cumle olarak korundu mu (default `LECTURE_AGGRESSIVE_CLEANUP=False`)
- [ ] **Yeni klasor duzeni Mac yolu**: G Drive Mac'te muhtemelen `/Volumes/GoogleDrive/Drive'ım/` veya benzeri — `DRIVE_RECORDS_BASE` constant'i Mac yoluna gore guncellenmesi gerekebilir. Eger Drive klient Mac'te `~/Library/CloudStorage/GoogleDrive-*/My Drive/` kullaniyorsa platform-ozel constant ayarla.
- [ ] **WAV dump Mac yolu**: `_save_wav` Mac'te de calisiyor mu (stdlib `wave` modulu cross-platform, sorun olmamali ama dogrula).
- [ ] **`--transcribe` ses tasima Mac yolu**: `.qta` / `.m4a` dosyalari iCloud Drive ile gelen tipik akista RawRecords'a tasima sirasinda permission/symlink sorunu olur mu.
- [ ] **Dosya ismi dialog (Mac)**: `_prompt_lecture_filename_macos` zaten Mac'te calisiyor; Windows ekledikten sonra Mac davranisi degismedi mi kontrol et.
- [ ] **Diarization (Meet) Mac'te**: TODO.md acik bir is olarak duruyor; Mac'te de ayni bozulma var mi gozle.

---

## Acik Isler

### Meet Dictation / Diarization (ek ozellik geri acma)

- [ ] **Diarization (Meet) tray'den gizlendi — opt-in olarak geri ac** (23 May 2026 itibariyla default davranis diarize'siz `_pick_file_and_meet_dictate_plain`; eski diarize'li `_pick_file_and_meet_dictate` ve speechbrain helper'lari kodda korunuyor ama tray'den cagrilmiyor).
  - Asagidaki diarize sorunu cozulduikten sonra opt-in olarak geri acilacak. Olasi yollar:
    1. Yeni tray menu item: "🎥 Meet Dictation (konusmaci ayir)..." -> eski `_pick_file_and_meet_dictate` callback'i.
    2. Veya CLI flag: `--diarize` (Win headless mode'a benzer).
    3. Veya plain akista "konusmaci sayisi ver" dialog'una "0 = ayirma" / "N>0 = N konusmaci ayir" gibi unified UX.
- [ ] **Diarization (Meet) duzgun calismiyor** (22 May 2026 raporu, hala acik — opt-in geri acmadan once cozulmeli).
  - Belirtiler: konusmacilar yanlis kumeleniyor, isimler yanlis ataniyor, tum transkript tek konusmaciya yapisiyor.
  - Platform: Windows, kayit tipi: Google Meet mp4.
  - Plan:
    1. Kucuk test dosyasiyla (2-3 dk, bilinen konusmaci sayisi) raw embedding output'unu logla — kume sayisi, mesafe matrisi, threshold karari.
    2. Tek-konusmaciya yapismanin sebebi: cluster sayisi 1'e mi dusuyor (low threshold) yoksa yanlis affinity mi? Ayirt et.
    3. Threshold/affinity tuning (cosine + dynamic threshold).
    4. Gerekirse pyannote-style turn boundary detection.
  - **Referans test dosyasi:** `G:\Drive'ım\Meet Recordings\RawRecords\Mustafa-Yiğit tivibu toplantısı.mp4` (32.5 MB, 16dk, TVBuy telif hakki toplantisi — Mustafa + Yigit iki belirgin konusmaci, diarize icin temiz benchmark).

### Konfigurasyon / Persist

- [ ] Konfigurasyon dosyasi (JSON/YAML) — hardcoded ayarlari disari cikar (threshold, model, device, hotkey, wake_word, `LECTURE_AGGRESSIVE_CLEANUP`, klasor yollari).
- [ ] Wake word disk'te persist (su an restart'ta default'a doner).
- [ ] Yeni wake word'lerin Whisper varyasyon regex'lerini otomatik genisletme.

### Test ve Regresyon

- [ ] Birim testleri (state machine, regex pattern, `extract_message`, audio buffer, `_dedupe_repeated_segments`, `_drop_low_confidence_segments`).
- [ ] Thread safety regresyon testi (state machine gecisleri).
- [ ] Mac auto-start dogrulamasi (CHANGELOG 22-23 May fix'leri sonrasi yeniden test).

### Cikti / UX

- [ ] Hedef pencere secimi: aktif pencere disinda secilen pencereye yazma.
- [ ] Multi-proje destegi: farkli wake word'ler ile farkli projelere yonlendirme.
- [ ] Windows notification toast (lecture bittiginde "Transkript hazir").
- [ ] macOS rumps notification (ayni amac).

---

_Son guncelleme: 2026-05-23 — TODO genel toparlama + CHANGELOG ayristirma._
