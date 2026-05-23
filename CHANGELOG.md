# CHANGELOG — VoiceDictation

Yapilan tum onemli degisikliklerin tarih sirasiyla kaydidir. Git log gercege uygun kaynak
olmaya devam eder; bu dosya kullanici-okur, gruplanmis ve gerekceli ozet sunar.

Format: tarih + baslik. Implementation detaylari icin commit ID referans verilir.

---

## 2026-05-23 (en gec) — CLAUDE.md sadelestirme + Drive Records index + Meet Recordings manuel arsiv

### CLAUDE.md sadelestirme (315 -> 247 satir)

- Windows + macOS Auto-Start kurulum reseteleri (~70 satir) **`docs/auto-start.md`**'ye birebir tasindi; CLAUDE.md'de 5-6 satir ozet + link kaldi. Kurulum bir kez yapilan i$ oldugu icin agent'in her session'da okumasi gerekmiyordu.
- Mac'te ilk session bloguu (0.5) ~15 sat -> 5 sat'a kisaltildi; tam Mac-spesifik test checklist'i zaten TODO.md'de var (daha detayli), CLAUDE.md sadece tarih + linkle proaktif hatirlatma yapar.
- Yeni: `docs/auto-start.md` (76 sat) — Win VBScript + Mac AppleScript .app kurulum, TCC izinleri (4 zorunlu izin tablosu), stale TCC entry temizligi, `.app` yeniden olusturma snippet'i.

### Drive Records paylasimli klasor index

- Yeni dosya: **`G:\Drive'ım\Records\index.md`** — Records klasoru birden cok proje tarafindan kullanilabilen merkezi depo oldugu icin agent'lara rehber. Icinde "Klasor Sozlugu" (VoiceDictation/ + RawRecords/, hangi proje yazar), "Aktif Projeler" (su an: VoiceDictation; repo yolu + akis tablosu + Drive sabitleri), "Cross-Project Referanslar" (bos placeholder), "Agent Talimatlari" (5 maddelik kural: yeni proje, yeni klasor, cross-project read, rename, index update) var.
- `Records/RawRecords/` ile `Meet Recordings/RawRecords/` karismasin diye index'te ayrim notu — birincisi VoiceDictation'in **otomatik yazdigi** islenmis ses, ikincisi Yigit'in **elle isimlendirip tasidigi** Meet ham kayitlari (mp4 video dahil).
- VoiceDictation/CLAUDE.md §1 Modlar > Lecture Mode altina tek satir not: "Records paylasimli — yeni klasor/davranis eklerken index.md'yi de guncelle."

### Meet Recordings manuel arsiv (repo disi)

- Drive'da `G:\Drive'ım\Meet Recordings\RawRecords\` alt klasoru olusturuldu (mevcut `Records/RawRecords/` ile ayni isim/mantik, Yigit'in elle yonettigi Meet ham kayit arsivi).
- Iki bekleyen Meet kaydi yeniden isimlendirilip tasindi:
  - `trz-rjon-krk (2026-05-01 13 56 GMT) (1)` (32.5 MB, 16dk) -> **`Mustafa-Yiğit tivibu toplantısı.mp4`** (TVBuy telif hakki / korsan koruma toplantisi, Govinet firmasi)
  - `trz-rjon-krk (2026-05-01 13 56 GMT) 2` (108.2 MB, 16dk) -> **`Mustafa-Yiğit Doğu.mp4`** (TVBuy projesi kapsaminda)
- Drive Meet otomasyonu mp4'leri uzantisiz dusurdugu icin `.mp4` uzantisi manuel eklendi — Windows'ta dogru ikon + tray "🎥 Meet Dictation..." filtresine dusus icin.
- CLAUDE.md Meet Dictation alt-bolumunde "Kaynak konum" ornegi guncellendi (Meet otomasyonu -> manuel isimlendirme -> Meet Recordings/RawRecords/ pattern'i).

---

## 2026-05-23 (gec) — Meet Dictation default davranisi: diarize'siz plain dictation

Kullanici talebi: "konusmaci ayirma artik olmasin. Meets dosyalari Dictation'dan gecirilsin
ses tarafi. Goruntu tarafi varsa ellenmesin, oldugu yerde birakilsin." Diarization, gunluk
Meet transkriptlerini sabote ediyor (TODO acik is: tek-konusmaciya yapisma, yanlis kume
sayisi); cozulene kadar default sade dictation'a alindi.

### Davranis degisikligi

- Tray menusu **"🎙 Meets Dictation (konuşmacı ayır)..."** → **"🎥 Meet Dictation..."** (Win + Mac).
- Callback yeni `_pick_file_and_meet_dictate_plain()`'e baglandi. Eski diarize'li
  `_pick_file_and_meet_dictate()` (line 2612+) ve speechbrain helper'lari (line 1293-1581)
  yerinde duruyor — opt-in flag/menu item ile ileride geri acilacak. Lazy import oldugu
  icin kullanilmadigi surece speechbrain/torch/sklearn yuku yok.

### Plain Meet Dictation akisi (`_pick_file_and_meet_dictate_plain`)

1. Dosya secici: mp4/webm/mov/mkv/avi/wav/mp3/m4a/aac/flac/ogg/opus/qta.
2. Isim dialog'u: `_prompt_lecture_filename` (lecture stop ile ayni helper, default = dosya stem).
3. Audio decode: Windows/Linux `faster_whisper.audio.decode_audio` (PyAV/libav), macOS `_load_audio_via_afconvert`.
4. `_save_wav(audio, RawRecords/<isim>.wav)` — 16 kHz mono PCM, stdlib `wave` (isim cakisirsa timestamp suffix).
5. `_transcribe_audio_path(audio, beam_size=5, word_timestamps=False)` — `_finalize_segments` B1-B4 temizligi otomatik.
6. `_write_lecture_markdown(VoiceDictation/<isim>.md, ..., header="Meet Dictation — <isim>")`.
7. `_open_in_editor(md_path)` — sonuc kullaniciya gosterilir.

### Orijinal dosya politikasi (kritik fark)

`--transcribe`/"Ses dosyasini dok..." akisi orijinal dosyayi `shutil.move` ile RawRecords'a
**tasiyor**. Meet Dictation **tasimaz** — orijinal mp4 (video dahil) bulundugu konumda
(tipik: `G:\Drive'ım\Meet Recordings\`) dokunulmadan kalir. Sebep: kullanici video tarafina
sonradan tekrar bakmak isteyebilir (ekran paylasimi, slide, demo), goruntu kaybi olmasin.

### CLAUDE.md

§1 Modlar bolumune yeni "Meet Dictation" alt-baslik eklendi. Konusmaci ayirma neden simdilik
kapali, akis adimlari, orijinal dosya politikasi documente edildi.

---

## 2026-05-23 — Yeni klasor duzeni + LIVE gecici + Stop dialog + Halusinasyon paket 2

### Klasor duzeni (CLAUDE.md §1 guncellendi)

- **G Drive'da Records altinda iki klasor:**
  - `G:\Drive'ım\Records\VoiceDictation\` — MD transkriptler (lecture final + `--transcribe` ciktilari)
  - `G:\Drive'ım\Records\RawRecords\` — islenen ses dosyalari (lecture WAV dump + tasinmis dis dosyalar)
- **Drive yoksa fallback:** `~/Desktop/VoiceDictation/{VoiceDictation,RawRecords}/`
  - `_ensure_writable_dir`: `os.makedirs` + `os.access(W_OK)` testi; OSError olursa Desktop'a dus
- **Lecture mode artik RAM-only DEGIL:** kayit bitince RAM buffer `RawRecords/<isim>.wav` (16-bit PCM mono 16kHz) olarak diske dokulur.
- **`--transcribe FILE` akisi:** islem sonrasi orijinal ses dosyasi `shutil.move` ile RawRecords'a TASINIR (silinmez; isim cakisirsa timestamp suffix).
- **Eski `~/Desktop/VoiceDictation_Lectures/` deprecate:** `_get_lectures_dir()` shim olarak `_get_voicedictation_dir()`'e yonlendirir; eski cagri yollari otomatik yeni yere gider.

### LIVE pass davranisi (gecici dosya, Drive'a yazilmaz)

- LIVE transcribe pipeline **ayni kaliyor** — kullanici lecture sirasinda anlik VS Code'da takip edebiliyor.
- **LIVE.md artik `tempfile.gettempdir()/voicedictation_live/` icinde** (Windows: `%LOCALAPPDATA%\Temp\voicedictation_live\`, Mac: `/tmp/voicedictation_live/`).
- Kayit bitince **LIVE.md silinir** — sadece final MD (Drive'da) + WAV (Drive'da) kalici. WAV zaten ses orijinaline geri donus saglar, LIVE'in arsivlenmesine gerek yok.
- Yeni helper: `_get_live_temp_dir()`.

### Dosya ismi dialog (Stop'ta, cross-platform)

- Lecture kapatildiginda `_prompt_lecture_filename(default_name)` cagrilir.
  - Mac: mevcut `_prompt_lecture_filename_macos` (osascript native).
  - Windows: yeni tkinter `simpledialog.askstring` (gizli root, modal, topmost).
  - Iptal/bos -> timestamp default kullanilir.
- Dialog `_bg` background thread'inin **basinda** acilir; isim alindiktan sonra WAV ve MD direkt o isimle yazilir (eski Mac-only rename mekanizmasi kaldirildi).

### Halusinasyon fix paket 2 (B1/B2/B3/B4)

22 Mayis paket 1 (commit `b83e384`) MLX yolunda sertlestirme yapti ama Tauron Bulusma ve Yeni Kayit 21 ornek dosyalari karsilastirildiginda hala 4 acik kalip vardi:

- **B1** — Tauron LIVE'da "onun icin" x11 zincirleme tekrar. Sebep: Windows/faster-whisper `quick_transcribe` cagrisinda `condition_on_previous_text` parametresi verilmiyor (faster-whisper default'u True). MLX yolu zaten False, parite saglandi.
- **B2** — Tauron Final'da "Evet." x10 tekrar. CLAUDE.md'deki "gercek 'evet evet evet' cevaplari korunur" kurali yuzunden artifact strip yakalamiyor. Coz: opt-in agresif tekrar dedupe (`LECTURE_AGGRESSIVE_CLEANUP=False` default, `--aggressive` flag ile acilir).
- **B3** — Tauron Final'da "Hacama bu" x4 + muglak "bizemle cozum" segmentleri. Sebep: dusuk-guven (`avg_logprob` cok dusuk, `no_speech_prob` yuksek) segmentler yakalanmiyor. Coz: Whisper segment metadata'sina dayali eşik filtresi (`_drop_low_confidence_segments`, default acik).
- **B4** — Yeni Kayit 21'de "Eee" x14 filler vocalization. Coz: 3+ ardarda filler regex tekillestirme (default acik, gercek cumle-ici tekrarlari etkilemez).

Yeni helper'lar: `_drop_low_confidence_segments`, `_dedupe_repeated_segments`, `_finalize_segments`, `_FILLER_RE`.
Yeni sabitler: `LECTURE_AGGRESSIVE_CLEANUP=False`, `LECTURE_CONF_NO_SPEECH=0.6`, `LECTURE_CONF_LOGPROB=-1.0`, `LECTURE_CONF_COMPRESSION=2.4`.
Yeni CLI: `--aggressive` flag (`_run_headless_transcribe`'a aktariliyor).

Test sonucu: 92sn kayit, hicbir spam/dedupe tetiklenmedi (kayit zaten temizdi), Windows CUDA'da 92x realtime final pass.

---

## 2026-05-22 — Sessizlik halusinasyon paket 1 (commit `b83e384`)

`Hakan Hoca Risk Yonetimi 20 Mayis` lecture vakasi (70dk "Altyazi M.K." tekrari) icin uc fix:

1. **`_vad_prefilter`**: MLX yoluna Silero VAD on-filtre + `SpeechTimestampsMap` timestamp remap. iPhone 11dk kaydinda %22 sessizlik kirpildi, 0.9sn ek islem.
2. **`condition_on_previous_text=False`**: her iki MLX cagrisinda (`quick_transcribe` + `_transcribe_audio_path`) — zincirleme tekrar imkansiz.
3. **`_strip_known_artifacts`**: lecture/file post-process icin GUVENLI artifact temizleyici. `_clean_transcription`'in aksine tekrar tespiti YAPMAZ, gercek "evet evet evet" cevaplarini korur.

---

## 2026-05-22 — Meet Dictation (commit `3e11f3d`)

speechbrain ECAPA-TDNN ile konusmaci ayirma (diarization) entegrasyonu. Tray menusunden "Meet kaydi sec...". Pipeline: dekod -> VAD -> Whisper word-level -> embedding -> clustering -> isim atama -> MD.

**Bilinen sorun:** Google Meet mp4 tek-kanal mix kayitlarinda diarization bozuk (kucuk threshold tum sesi tek kumeye atiyor). Cozulmedi, TODO'da takipte.

---

## 2026-05-22 — PID lockfile (commit `c5dbc5e`)

Daemon ve headless `--transcribe` ayni anda calistiginda GPU/CUDA context cakismasi. Coz: `logs/dictation.pid` lockfile; `--transcribe` calistirilirken daemon varsa reddet, kullaniciya "once tray'den Cikis" mesaji.

---

## 2026-05-19 / 2026-05-16 — Lecture kalite tuning

- **`72a2589`**: MLX `quick_transcribe` beam_size hatasi fix + try/except guard.
- **`208578a`**: dictation ve LIVE beam_size 1 -> 3 (kalite iyilestirmesi, RTX GPU'da hiz farki yok cunku decoder yuku encoder yaninda ihmal edilebilir).
- **`367e985`**: LIVE beam=3, popup dosya isimlendirme (Mac yolunda eklenmis), MLX crash fix.

---

## 2026-04-27 — Whisper kelime duzeltmesi

`4b5de3a`: Whisper transkriptlerde "Zugzwang" gibi kelimelerin dogru yazilmasi icin `_apply_word_corrections`.

---

## 2026-04-26 — Public release + macOS test paketi

**Ana commit'ler:**
- `dcd3756`: README + CLAUDE.md macOS izin tablosu detaylandirma
- `5dd5246`: macOS test paketi — triple-tap reset (Caps Lock long-press yerine), tkinter -> osascript native picker, AppleScript .app launcher (`scripts/VoiceDictation.app`)
- `60ceb29`: Toplanti modu iyilestirmeleri (tray hiyerarsi: Toplanti/Ayarlar submenu), wake word configurable
- `d7531c8`: Editor opener cross-platform (`_open_in_editor` VS Code -> sistem default -> clipboard fallback) + Turkce lokalizasyon notu
- `a2d49db`: Public open-source hazirligi — MIT lisansi, `.mcp.json` untrack
- `3676bac`: Toplanti/ders modu — RAM-only canli transkript + dosyadan cevirme

macOS Tahoe TCC kisitlamalari nedeniyle Login Items + AppleScript .app secildi (LaunchAgent + start.sh + ad-hoc imzali shell .app denemeleri TCC tarafindan sessizce reddedildi).

---

## 2026-03-30 / 2026-03-23 — Audio buffer optimizasyon

- `3194a1c`: Wake word default kapali, listen buffer optimizasyonu, carry-over azaltma.
- `873374a`: Listen buffer ~30sn siniri (arka plan ses birikmesi onlendi).

---

## 2026-03-21 — Long-press reset + wake word toggle

- `d988f8d`: Windows'ta F13 long-press (1.25sn) kayit iptal.
- `bcb0fd0`: Anahtar kelime tray toggle.

---

## 2026-03-19 — GUI

- `c977728`: Windows GUI pystray sistem tepsisi (tkinter window'dan gecis).
- `e7dbf0a`: macOS rumps menu bar.

---

## 2026-03-17 — Audio sistem iyilestirmeleri

- `33639b6`: Halusinasyon filtresi yeniden tasarlandi — uzun metinler artik korunuyor.
- `bdb7d14`: Log rotation, audio watchdog, wake word backoff.

---

## 2026-03-15 / 2026-03-14 — Cross-platform + MLX

- `c05412a`: Halusinasyon filtresi eklendi (mlx-whisper sessizlik ciktilari).
- `ffaced8`: macOS MLX-whisper entegrasyonu, proje reorganizasyonu.
- `09928fb`: Cross-platform support, logging system, bug fixes.
- `08963d8`: Initial commit — VoiceDictation standalone project.

---

_Daha eski degisiklikler icin `git log --oneline` veya commit hash'leri ile inceleyin._
