# TODO — VoiceDictation

## Proje Kurulumu

- [x] BMAD kurulumu (`_bmad/` dizini ve `.claude/commands/`)
- [x] Private GitHub repo olustur ve push et
- [x] README.md olustur (kullanim kilavuzu, kurulum talimatlari)

## Cross-Platform Setup

- [x] Windows kurulum testi (git clone + setup.bat + start.bat)
- [ ] macOS kurulum testi (git clone + setup.sh)
- [x] macOS icin `start.sh` script'i olustur (start.bat karsiligi)
- [x] setup.sh: macOS portaudio bagimliligi ekle (`brew install portaudio`)
- [x] CUDA kurulum notu dokumante et (Windows icin CUDA Toolkit + cuBLAS)
- [x] macOS'ta CPU fallback: DEVICE otomatik algilama ekle (CUDA yoksa CPU'ya dus)

## MacBook Pro Entegrasyonu

- [ ] macOS hotkey testi: Ctrl+Option+R zaten tanimli, dogrula
- [ ] Touchpad gesture / alternatif key binding arastirmasi
- [ ] macOS mikrofon izni (Privacy & Security) dokumantasyonu
- [x] macOS ses geri bildirimi: winsound alternatifi (subprocess afplay)

## Bug Fix / Iyilestirme

- [ ] Stop word checker: Whisper "Zugzwang" varyasyonlari icin regex genisletme (yeni varyasyonlar geldikce)
- [ ] Stop word checker: Daha verimli tetikleme stratejisi (gereksiz transcribe azaltma)
- [ ] Thread safety regresyon testi yaz (state machine gecisleri)
- [ ] Mesaj icinde "Zugzwang" gecince erken kesme sorunu — context-aware stop word algilama

## Gelecek

- [ ] Konfigurasyon dosyasi (JSON/YAML) — hardcoded ayarlari disari cikar (threshold, model, device, hotkey)
- [ ] Python logging modulu — print yerine seviyeli loglama (DEBUG/INFO/WARNING)
- [ ] Birim testleri (state machine, regex pattern, extract_message, audio buffer)
- [ ] Windows baslatma: Startup klasorune .vbs koyarak otomatik baslat
- [ ] Multi-proje destegi: farkli wake word'ler ile farkli projelere yonlendirme
