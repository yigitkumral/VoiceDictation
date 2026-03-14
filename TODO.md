# TODO — VoiceDictation

## Proje Kurulumu

- [ ] BMAD kurulumu (`_bmad/` dizini ve `.claude/commands/`)
- [ ] Private GitHub repo olustur ve push et
- [ ] README.md olustur (kullanim kilavuzu, kurulum talimatlari)

## Cross-Platform Setup

- [ ] Windows kurulum testi (git clone + setup.bat + start.bat)
- [ ] macOS kurulum testi (git clone + setup.sh)
- [ ] macOS icin `start.sh` script'i olustur (start.bat karsiligi)
- [ ] setup.sh: macOS portaudio bagimliligi ekle (`brew install portaudio`)
- [ ] CUDA kurulum notu dokumante et (Windows icin CUDA Toolkit + cuBLAS)
- [ ] macOS'ta CPU fallback: DEVICE otomatik algilama ekle (CUDA yoksa CPU'ya dus)

## MacBook Pro Entegrasyonu

- [ ] macOS hotkey testi: Ctrl+Option+R zaten tanimli, dogrula
- [ ] Touchpad gesture / alternatif key binding arastirmasi
- [ ] macOS mikrofon izni (Privacy & Security) dokumantasyonu
- [ ] macOS ses geri bildirimi: winsound alternatifi (simpleaudio veya subprocess afplay)

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
