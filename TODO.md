# TODO — VoiceDictation

## Proje Kurulumu

- [x] BMAD kurulumu (`_bmad/` dizini ve `.claude/commands/`)
- [x] Private GitHub repo olustur ve push et
- [x] README.md olustur (kullanim kilavuzu, kurulum talimatlari)

## Cross-Platform Setup

- [x] Windows kurulum testi (git clone + setup.bat + start.bat)
- [x] macOS kurulum testi (git clone + setup.sh)
- [x] macOS icin `start.sh` script'i olustur (start.bat karsiligi)
- [x] setup.sh: macOS portaudio bagimliligi ekle (`brew install portaudio`)
- [x] CUDA kurulum notu dokumante et (Windows icin CUDA Toolkit + cuBLAS)
- [x] macOS'ta MLX-whisper entegrasyonu (Apple Silicon GPU destegi)
- [x] Script'leri `scripts/` klasorune tasi (proje root temizligi)

## MacBook Pro Entegrasyonu

- [x] macOS hotkey: Caps Lock double-tap toggle (400ms aralik)
- [x] macOS mikrofon + accessibility izinleri dogrulanmis
- [x] macOS ses geri bildirimi: winsound alternatifi (subprocess afplay)
- [x] Ses seviyesi arttirildi (volume 0.04 -> 0.25)

## Bug Fix / Iyilestirme

- [x] MLX GPU crash fix: transcribe_lock ile thread-safe GPU erisimi
- [x] Halusinasyon filtresi: sessiz audio transcribe'a gonderilmez (_has_speech)
- [x] extract_message fix: ilk wake word'den onceki mesaji al (Zugzwang temizleme)
- [x] Python logging modulu — print yerine seviyeli loglama (DEBUG/INFO/WARNING)
- [ ] Stop word checker: Whisper "Zugzwang" varyasyonlari icin regex genisletme (yeni varyasyonlar geldikce)
- [ ] Thread safety regresyon testi yaz (state machine gecisleri)

## Gelecek

- [ ] Konfigurasyon dosyasi (JSON/YAML) — hardcoded ayarlari disari cikar (threshold, model, device, hotkey)
- [ ] Birim testleri (state machine, regex pattern, extract_message, audio buffer)
- [ ] Windows baslatma: Startup klasorune .vbs koyarak otomatik baslat
- [ ] macOS baslatma: Login Items veya LaunchAgent ile otomatik baslat
- [ ] Hedef pencere secimi: herhangi bir pencereye yazma (aktif pencere disinda)
- [ ] Multi-proje destegi: farkli wake word'ler ile farkli projelere yonlendirme
