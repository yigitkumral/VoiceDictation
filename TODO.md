# TODO — VoiceDictation

## Proje Kurulumu

- [x] BMAD kurulumu (`_bmad/` dizini ve `.claude/commands/`)
- [x] GitHub repo olustur ve push et
- [x] README.md olustur (kullanim kilavuzu, kurulum talimatlari)
- [x] MIT lisans + LICENSE dosyasi (public hazirligi)
- [x] README.md'ye Turkce lokalizasyon notu (proje Turkce konusma tanimaya ozel)
- [x] `.mcp.json` git tracking'den cikarildi (kullaniciya ozel filesystem path icerir), `.mcp.json.example` template ile yerine
- [x] `.gitignore`: `_bmad-output/` eklendi (BMAD agent ciktilari kisisel olabilir)
- [x] Guvenlik taramasi: kod + git history (API key/password/secret yok, temiz)

## Cross-Platform Setup

- [x] Windows kurulum testi (git clone + setup.bat + start.bat)
- [x] macOS kurulum testi (git clone + setup.sh)
- [x] macOS icin `start.sh` script'i (start.bat karsiligi)
- [x] setup.sh: macOS portaudio bagimliligi (`brew install portaudio`)
- [x] CUDA kurulum notu dokumante (Windows icin CUDA Toolkit + cuBLAS)
- [x] macOS'ta MLX-whisper entegrasyonu (Apple Silicon GPU destegi)
- [x] Windows auto-start: Startup klasorunde `start.vbs` ile gizli pencere
- [x] macOS auto-start: Login Items + AppleScript .app launcher (`scripts/VoiceDictation.app`)
  - LaunchAgent ve `start.sh` Login Items denendi, macOS Tahoe TCC kisitlamasi nedeniyle calismadi
  - AppleScript .app `Automation` kategorisinde oldugu icin Desktop'a erisebiliyor
- [x] Script'leri `scripts/` klasorune tasi (proje root temizligi)

## Hotkey + GUI

- [x] Windows: F13 (Logitech G502 sniper button) toggle
- [x] macOS: Caps Lock double-tap toggle (400ms aralik)
- [x] Reset: Windows long-press (F13 1.25sn) / macOS triple-tap (Caps Lock x3 400ms penceresi)
  - Caps Lock OS-level toggle key oldugundan long-press tetiklenemiyor; triple-tap kullanilir
  - RECORDING durumunda 2. tap'tan sonra DOUBLE_TAP_INTERVAL gecikme (3. tap iptal edebilsin)
- [x] Cikis hotkey'i kaldirildi (Cmd+Alt+Q macOS oturum kapatma sistem kisayoluyla cakisiyordu)
- [x] macOS mikrofon + accessibility izinleri dogrulanmis
- [x] Windows GUI: pystray sistem tepsisi ikonu (tkinter yerine)
- [x] macOS GUI: rumps menu bar ikonu
- [x] Tray menusu hiyerarsik yapi: 🎤 Toplanti / ⚙ Ayarlar submenu, ↺ Sifirla, Cikis

## Wake Word

- [x] Default wake word: "Diktasyon"
- [x] Whisper varyasyonlari icin regex (diktasyon, diktason, diktatsyon, dictation, ...)
- [x] Tray menusunden wake word degistirilebilir (tkinter dialog Windows, rumps Window macOS)
- [x] Anahtar kelime dinleme aciksa wake word ile baslatma + durdurma
- [x] "Diktasyon [mesaj] Diktasyon" tek nefes modu
- [x] INITIAL_PROMPT'tan "Diktasyon"/"Zugzwang" cikarildi (Whisper false-positive olarak hayal ediyordu)
- [x] Whisper "Diktasyon Diktasyon" tekrar bug fix: 2 match + bos mesaj durumu artik tek wake gibi davraniyor (start_recording)
- [x] Tum "Zugzwang" referanslari "Diktasyon"a guncellendi (kod, README, CLAUDE, TODO, banner)
- [ ] Wake word degisikliklerinin disk'te persist edilmesi (su an restart'ta default'a doner)
- [ ] Yeni wake word'lerin Whisper varyasyon regex'lerini otomatik genisletme

## Lecture / Toplanti Modu

- [x] Tray menusunden toplanti kaydi baslat/durdur (F13 lecture sirasinda ignore)
- [x] **RAM-only**: ses dosyasi DISKE YAZILMAZ, sadece transkript MD dosyalari
- [x] Canli transkript (LIVE.md): VAD-bazli cumle akisi, turbo + beam=1
  - LIVE_SILENCE_DURATION: 1.5sn -> **0.8sn** (dogal konusma araligi)
  - LIVE_MAX_CHUNK_SECONDS: 25sn -> **12sn** (surekli konusan icin akiskan canli yazim)
  - Yeni `LECTURE_LIVE_VAD_THRESHOLD = 0.025` (mac dahili mic baseline 0.005-0.015 oldugundan SILENCE_THRESHOLD 0.008 cumle araligi yakalayamiyordu)
- [x] Final transkript (.md): kayit bitince tum ses, beam=5 ile yuksek kalite
- [x] Live thread'in stop'ta join edilmesi (final paragraf "Final transkript hazir" sonrasi yazilmiyor)
- [x] Tek kapanma sesi (ikinci sound_sent kaldirildi)
- [x] Tray ikonu lecture aktifken mor renk
- [x] Editor otomatik acma (canli MD'yi VS Code'da)
- [x] Tani log'u: stop'ta chunks/samples buffer durumu
- [x] Transkript MD'lere kapanis footer'i: `Transkript tamamlandi. Sure: ... • Model: ...`

## Dosyadan Transkript

- [x] Tray menusunden "Ses dosyasini dok..." — Windows: tkinter, **macOS: osascript native picker**
  - Daha onceki tkinter macOS'ta rumps ile main-thread/GIL deadlock yapip SIGABRT crash ediyordu
- [x] CLI alternatif: `--transcribe FILE` (headless, daemon gereksiz)
- [x] AAC/MP3/WAV/M4A/FLAC/OGG/MP4 destegi
- [x] **macOS'ta `.qta` (Voice Memos lossless) destegi** + AIFF/CAF
- [x] **macOS'ta ffmpeg yerine `afconvert` (native)** — ffmpeg dependency'si kaldirildi
  - mlx_whisper'in dahili load_audio'su ffmpeg gerektiriyordu; afconvert ile pre-load edip numpy verilirse atlanir
- [x] Cikti: ses dosyasi yaninda `.md` + Desktop/VoiceDictation_Lectures kopyasi
- [x] 80dk AAC -> ~4dk islem (CUDA + turbo, ~20x realtime)
- [x] **iPhone Voice Memos akisi netlestirildi (22 May 2026)**: `.m4a` (AAC) ve `.qta` (ALAC veya AAC, QuickTime container) her iki platformda dogrudan calisiyor; Windows'ta PyAV ile decode (ffmpeg PATH'i gerekmez). CLAUDE.md'de adim-adim akis dokumante edildi.

## Meet Dictation / Konusmaci Ayirma (Diarization)

- [x] speechbrain ECAPA-TDNN entegrasyonu (commit `3e11f3d`)
- [x] Tray menusunden "Meet kaydi sec..." dosya secici
- [x] Pipeline: dekod → VAD → Whisper transcribe (word-level) → embedding → clustering → isim atama → MD
- [ ] **BOZULMA: Diarization duzgun calismiyor (22 May 2026 — kullanici raporu).**
  - **Belirtiler (kullanicidan, 3'u birden):** konusmacilar yanlis kumeleniyor, isimler yanlis atamiyor, tum transkript tek konusmaciya yapisiyor.
  - **Platform:** Windows. **Kayit tipi:** Google Meet (mp4).
  - **En olasi kok-sebepler (siralanmis):**
    1. Meet kaydi tek-kanal mix — herkesin sesi ayni track'te; ECAPA-TDNN embedding'leri yeterince ayrismiyor (ozellikle benzer ses tonlu kisilerde). Speaker turn boundary'leri Whisper word-timestamp'lerinden cikartiliyor; konusmaci degisimleri hatali yerlerde tespit ediliyor olabilir.
    2. Clustering threshold/parametre uyumsuz (su an muhtemelen sabit AgglomerativeClustering threshold) → kucuk farklari ayni kume, tum sesi tek kume yapiyor.
    3. Embedding penceresi cok kisa (1-2sn) veya cok uzun: kisa pencerelerde gurultu/sessizlik embedding'i bozar; uzun pencerelerde turn'ler atlanir.
    4. Isim eslestirme: aktif kume merkezleri yerine yanlis temsilci embedding'lerle eslestiriliyor olabilir.
  - **Plan:**
    1. Once kucuk bir test dosyasiyla (2-3 dk Meet kaydi, bilinen 2-3 konusmaci) raw embedding output'unu logla — kume sayisi, mesafe matrisi, threshold karari.
    2. Tek-konusmaciya yapismanin sebebi: cluster sayisi 1'e dusuyor mu (low threshold) yoksa hepsi ayni kumeye mi atilizyor (yanlis affinity)? Logdan ayirt et.
    3. Threshold/affinity tuning (cosine + dynamic threshold).
    4. Gerekirse pyannote-style turn boundary detection (Whisper word boundary'leri yerine VAD + voice activity diff).
  - **Referans dosya:** kullanicinin Drive'inda `Meet Recordings/trz-rjon-krk (2026-05-01 13 56 GMT) (1)` — test icin elde.

## Editor Entegrasyonu

- [x] `_open_in_editor` cross-platform sirali fallback (VS Code > sistem default > clipboard)
- [x] `VOICEDICTATION_EDITOR` ENV var ile override (notepad++/obsidian/typora/...)
- [x] `VOICEDICTATION_EDITOR=none` ile sadece clipboard'a kopyalama
- [x] Windows'ta `code.cmd` onceligi (Code.exe yerine — yeni window degil, mevcut instance'a tab olarak ekler)
- [x] shutil.which ile editor PATH dogrulamasi

## Bug Fix / Iyilestirme

- [x] MLX GPU crash fix: transcribe_lock ile thread-safe GPU erisimi
- [x] Halusinasyon filtresi: sessiz audio transcribe'a gonderilmez (_has_speech)
- [x] Halusinasyon yuzdesi yumusatildi: 20+ kelimede %75, 10-19'da %65 (eski %60 gercek konusmalari yutu yordu)
- [x] extract_message fix: ilk wake word'den onceki mesaji al
- [x] Python logging modulu (DEBUG/INFO/WARNING, gunluk rotate)
- [x] Audio watchdog: uyku/hibernate sonrasi stream'i otomatik yeniden baslat
- [x] Wake word backoff (gereksiz transcribe'i azalt)
- [x] Listen buffer sinir (~30sn): arka plan ses birikmesi onlendi
- [x] Listen buffer carry-over azaltma (kayit baslarken son 1sn yeterli)
- [x] **Sessizlik halusinasyonu fix (22 May 2026)** — vaka: `Hakan Hoca Risk Yonetimi 20 Mayis.md` (70dk "Altyazi M.K." tekrar). Uc fix uygulandi:
  - `_vad_prefilter`: MLX yoluna Silero VAD on-filtre + `SpeechTimestampsMap` ile timestamp remap (faster-whisper.vad helper'lari, ekstra dep yok)
  - `condition_on_previous_text=False` her iki MLX cagrisinda (quick_transcribe + _transcribe_audio_path) — zincirleme tekrar imkansiz
  - `_strip_known_artifacts`: lecture/file post-process icin GUVENLI artifact temizleyici (`_clean_transcription`'in tekrar tespitini yapmaz, gercek "evet evet" cevaplarini korur)
  - Windows venv'de syntax + VAD prefilter testi OK (iPhone 11dk kaydinda %22 sessizlik kirpildi, 0.9sn ek islem)
- [ ] **TO DO: Mac'te gercek bir lecture kaydiyla yukaridaki fix'i uctan uca dogrula** (mikrofon uzakta + uzun sessizlikli senaryo). Beklenti: artifact spam yerine bos veya minimal segmentler.
- [ ] Thread safety regresyon testi yaz (state machine gecisleri)
- [ ] Yeni Whisper varyasyonlari geldikce wake word regex'i genislet

## macOS Test Sonuclari (2026-04-26)

Tum testler macOS Tahoe 26.3 + Apple Silicon + MLX uzerinde gecti:

- [x] **Hotkey diktasyon** — Caps Lock x2 toggle calisti
- [x] **Triple-tap reset** — Caps Lock x3 ile kayit iptal calisti (long-press fix)
- [x] **Wake word** — "Diktasyon" + Whisper varyasyonlari yakaladi
- [x] **Tek nefes modu** — `Diktasyon [mesaj] Diktasyon` calisti
- [x] **Lecture mode** — RAM-only canli MD + final pass calisti, MLX 40x realtime
- [x] **Dosyadan transkript** — m4a + qta (Voice Memos), afconvert ile, osascript picker
- [x] **Anahtar kelime degistirme** — rumps Window dialog
- [x] **Halusinasyon filtresi** — sessiz kayit `Altyazi M.K.` vb. yakaladi
- [x] **Tray hiyerarsi** — rumps submenu (🎤 Toplanti / ⚙ Ayarlar)
- [x] **Auto-start** — Login Items + AppleScript .app launcher
  - Mac restart sonrasi otomatik baslama dogrulandi
  - Caps Lock x2 ilk denemede calisti (Input Monitoring + Accessibility izinleri verildi: VoiceDictation + applet)

**Tespit edilen ve duzeltilen sorunlar bu session'da:**
1. macOS Caps Lock long-press tetiklenmiyor (OS toggle key) → triple-tap kullanildi
2. INITIAL_PROMPT'taki "Diktasyon" Whisper'i hayal etmeye zorluyor → cikarildi
3. Whisper "Diktasyon" demeye karsi "Diktasyon Diktasyon" yaziyor → tekrar handler eklendi
4. Mac mic baseline 0.005-0.015 oldugundan lecture VAD cumle araligi yakalayamiyor → ayri threshold (0.025)
5. Lecture VAD timing default'lari surekli konusmacida force-flush'a takilmis → 0.8sn / 12sn
6. mlx_whisper file transcribe icin ffmpeg gerekiyor, mac'te yok → afconvert (native) ile pre-load
7. tkinter file picker rumps ile main-thread cakismasi yapip SIGABRT crash → osascript native picker
8. Voice Memos lossless `.qta` formati picker'da yoktu → eklendi
9. Cmd+Alt+Q quit hotkey macOS oturum kapatma kisayoluyla cakisiyor → kaldirildi
10. macOS LaunchAgent + Login Items + start.sh + ad-hoc imzali shell .app — TCC kisitlamasi nedeniyle Desktop'a erisim sessizce reddediliyor → AppleScript .app launcher (`Automation` kategorisi calisir)
11. Login Items'tan baslatilan .app'in Caps Lock'u yakalamasi icin **Input Monitoring** ve **Accessibility** izinleri "VoiceDictation" + "applet" entry'lerine verilmeli (System Settings -> Privacy & Security)

## Gelecek (Yapilacaklar)

- [ ] Konfigurasyon dosyasi (JSON/YAML) — hardcoded ayarlari disari cikar (threshold, model, device, hotkey, wake_word)
- [ ] Wake word disk'te persist (config.json)
- [ ] Birim testleri (state machine, regex pattern, extract_message, audio buffer)
- [ ] Hedef pencere secimi: herhangi bir pencereye yazma (aktif pencere disinda)
- [ ] Multi-proje destegi: farkli wake word'ler ile farkli projelere yonlendirme
- [ ] Windows: notification toast (lecture bittiginde "Transkript hazir" bildirimi)
- [ ] macOS: rumps notification (ayni amac)
