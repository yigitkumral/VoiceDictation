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
- [x] macOS auto-start: LaunchAgent plist ile login sonrasi otomatik calisma
- [x] Script'leri `scripts/` klasorune tasi (proje root temizligi)

## Hotkey + GUI

- [x] Windows: F13 (Logitech G502 sniper button) toggle
- [x] macOS: Caps Lock double-tap toggle (400ms aralik)
- [x] Long-press reset (F13 1.25sn basili tutunca kayit iptal)
- [x] macOS mikrofon + accessibility izinleri dogrulanmis
- [x] Windows GUI: pystray sistem tepsisi ikonu (tkinter yerine)
- [x] macOS GUI: rumps menu bar ikonu
- [x] Tray menusu hiyerarsik yapi: 🎤 Toplanti / ⚙ Ayarlar submenu, ↺ Sifirla, Cikis

## Wake Word

- [x] Default wake word: "Diktasyon" (eskiden "Zugzwang")
- [x] Whisper varyasyonlari icin regex (diktasyon, diktason, diktatsyon, dictation, ...)
- [x] Tray menusunden wake word degistirilebilir (tkinter dialog Windows, rumps Window macOS)
- [x] Eski "Zugzwang" yedek regex'i hala mevcut (set_wake_word("zugzwang") ile aktif)
- [x] Anahtar kelime dinleme aciksa wake word ile baslatma + durdurma
- [x] "Zugzwang [mesaj] Zugzwang" tek nefes modu (artik "Diktasyon [mesaj] Diktasyon")
- [ ] Wake word degisikliklerinin disk'te persist edilmesi (su an restart'ta default'a doner)
- [ ] Yeni wake word'lerin Whisper varyasyon regex'lerini otomatik genisletme

## Lecture / Toplanti Modu

- [x] Tray menusunden toplanti kaydi baslat/durdur (F13 lecture sirasinda ignore)
- [x] **RAM-only**: ses dosyasi DISKE YAZILMAZ, sadece transkript MD dosyalari
- [x] Canli transkript (LIVE.md): VAD-bazli cumle akisi (1.5sn sessizlik), turbo + beam=1
- [x] Final transkript (.md): kayit bitince tum ses, beam=5 ile yuksek kalite
- [x] Live thread'in stop'ta join edilmesi (final paragraf "Final transkript hazir" sonrasi yazilmiyor)
- [x] Tek kapanma sesi (ikinci sound_sent kaldirildi)
- [x] Tray ikonu lecture aktifken mor renk
- [x] Editor otomatik acma (canli MD'yi VS Code'da)
- [x] Tani log'u: stop'ta chunks/samples buffer durumu

## Dosyadan Transkript

- [x] Tray menusunden "Ses dosyasini dok..." (tkinter file picker)
- [x] CLI alternatif: `--transcribe FILE` (headless, daemon gereksiz)
- [x] AAC/MP3/WAV/M4A/FLAC/OGG/MP4 destegi (PyAV uzerinden)
- [x] Cikti: ses dosyasi yaninda `.md` + Desktop/VoiceDictation_Lectures kopyasi
- [x] 80dk AAC -> ~4dk islem (CUDA + turbo, ~20x realtime)

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
- [ ] Thread safety regresyon testi yaz (state machine gecisleri)
- [ ] Yeni Whisper varyasyonlari geldikce wake word regex'i genislet

## Bekleyen Testler — macOS

Tum yeni ozellikler **Windows'ta test edildi**, macOS'ta henuz test edilmedi:

- [ ] **macOS'ta lecture mode** — RAM-only kayit, canli MD akisi, final pass
  - rumps thread'inden tkinter file dialog acilabiliyor mu? (macOS Cocoa main-thread gereksinimi)
  - mlx-whisper ile lecture mode performansi (Apple Silicon GPU, beam=5)
  - Uzun kayitlarda (1+ saat) RAM tuketimi
- [ ] **macOS'ta dosyadan transkript** — tray "Ses dosyasini dok..." menusu
- [ ] **macOS'ta editor opener** — sistem default fallback (`open` komutu)
- [ ] **macOS'ta wake word degistirme** — rumps Window dialog
- [ ] **macOS'ta tray hiyerarsi** — submenu yapisi rumps'ta nasil gozukuyor

## Gelecek (Yapilacaklar)

- [ ] Konfigurasyon dosyasi (JSON/YAML) — hardcoded ayarlari disari cikar (threshold, model, device, hotkey, wake_word)
- [ ] Wake word disk'te persist (config.json)
- [ ] Birim testleri (state machine, regex pattern, extract_message, audio buffer)
- [ ] Hedef pencere secimi: herhangi bir pencereye yazma (aktif pencere disinda)
- [ ] Multi-proje destegi: farkli wake word'ler ile farkli projelere yonlendirme
- [ ] Windows: notification toast (lecture bittiginde "Transkript hazir" bildirimi)
- [ ] macOS: rumps notification (ayni amac)
