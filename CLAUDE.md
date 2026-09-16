# CLAUDE.md — VoiceDictation

Ajan talimatları (Claude Code ve Codex). Projenin ne olduğu, verinin nerede durduğu ve nasıl başlatıldığı [README.md](README.md) dosyasındadır; her oturumda önce onun **Yerel dosyalar** bölümünü oku.

## 1. Mac'te ilk oturum

Mac'te açılan ilk oturumda, ilk yanıtta şunu hatırlat: son Mac doğrulaması 26 Nisan 2026'da yapıldı, sonraki bütün değişiklikler yalnız Windows'ta doğrulandı. Yiğit'e [docs/TODO.md](docs/TODO.md) içindeki "Mac'te ilk oturum" listesini öner.

## 2. Kurallar

- **Commit:** Commit'ten önce Yiğit'in onayını al. `master` dalına yalnız Yiğit push eder; başka bir katkıcı adına çalışıyorsan `feature/<konu>` dalı aç ve PR gönder.
- **Kullanım değişmez:** F13 / Caps Lock x2, "Diktasyon" wake word, tray menüsü, `--transcribe` ve `--aggressive` bayrakları, transkript biçimi. Bunları değiştiren iş yeni özelliktir; ayrı onay ister.
- **Veri gizliliği:** `data/` altındaki transkript ve ses dosyalarından, `.local/logs/` içindeki loglardan yalnız ad, boyut ve sayı bilgisini oku. Yiğit istemedikçe içeriklerini okuma veya raporlama.
- **Daemon:** Çalışıyor olabilir. Yalnız Yiğit'in bilgisiyle durdur (tray → Çıkış). Daemon açıkken `dictation.py`'yi ikinci kez başlatma. `--transcribe` zaten reddedilir (PID kilidi): aynı GPU'da iki model çakışır. Kod değişikliğini `venv\Scripts\python -m py_compile dictation.py` ile denetle.
- **Git temizliği:** Programı kullanmak git durumunu değiştirmez. Çalışma çıktıları yalnız `data/` (değerli) veya `.local/` (yeniden üretilir) altına yazılır; ikisi de ignore'ludur. Yeni bir çıktı türü de bu iki klasörden birine gider.
- **Yollar tek yerde:** Tüm yollar `dictation.py` başındaki yol bloğundadır (`BASE_DIR`, `DATA_DIR`, `INBOX_DIR`, `AUDIO_DIR`, `TRANSCRIPTS_DIR`, `LOCAL_DIR`, `_LOG_DIR`, `MODELS_DIR`). Repo dışına veri yazan kod ekleme.
- **Belge bakımı:** Yol, klasör, menü veya CLI değiştiren commit, aynı commit içinde README'deki "Yerel dosyalar" tablosunu ve [docs/nasil-calisir.md](docs/nasil-calisir.md) dosyasını günceller. Teslimden önce şu komut boş dönmeli:

  ```bash
  grep -n -e "Driv[e]'" -e "Meet Recording[s]" -e "RawRecord[s]" -e "_Lecture[s]" README.md CLAUDE.md dictation.py docs/*.md | grep -v "^docs/CHANGELOG"
  ```

- **İş takibi:** Açık işler [docs/TODO.md](docs/TODO.md) dosyasına, tamamlananlar [docs/CHANGELOG.md](docs/CHANGELOG.md) dosyasına (en yeni üstte) yazılır. Bu dosyada tarihçe tutulmaz.
- **Araştırma kayıtları:** Çok ajanlı analiz ve uygulama turlarının brif ve sonuçları `docs/sessions/YYYY-MM-DD-<konu>/` altında durur.
- **Dil ve üslup:** Yiğit ile Türkçe konuş. Kod yorumlarını mevcut üsluba uyarak ASCII Türkçe yaz. Kütüphane API'sinden emin değilsen önce Context7 ile doğrula.

## 3. Mimari özeti

- **Tek dosya:** Uygulamanın tamamı `dictation.py`'dedir. Durum makinesi `LISTENING → RECORDING → PROCESSING → COOLDOWN` (mutex korumalı). Ayrı mod ekseni: dikte ↔ toplantı (lecture).
- **Ses yolu:** sounddevice → numpy tamponu → Whisper → pano → pynput ile yapıştır + Enter.
- **STT:** Windows'ta faster-whisper (CUDA, yoksa CPU), macOS'ta mlx-whisper (Silero VAD ön filtresiyle). Model: turbo. Dikte `beam=3`, toplantı ve dosya transkripti `beam=5`.
- **Arayüz:** Windows'ta pystray tepsi simgesi, macOS'ta rumps menü çubuğu. Durum renkleri: yeşil hazır, kırmızı kayıt, sarı işleniyor, mor toplantı.
- **Kapalı kodlar:** Konuşmacı ayırma (speechbrain) kodu duruyor ama tray'den çağrılmıyor. `file_queue.py` dış istemci kuyruğudur, daemon'a bağlı değil. Testler: `venv\Scripts\python -m unittest discover -s tests`.

## 4. Belge haritası

| Belge | Görevi |
|---|---|
| [README.md](README.md) | İnsan girişi, kurulum özeti, kullanım, **yerel dosyalar tablosu** |
| [docs/nasil-calisir.md](docs/nasil-calisir.md) | Mod akışları, tray menüsü, çıktı biçimi, halüsinasyon katmanları, ayarlar |
| [docs/kurulum.md](docs/kurulum.md) | Kurulum, otomatik başlatma, macOS izinleri, yeni cihaza taşıma |
| [docs/TODO.md](docs/TODO.md) | Açık işler, Mac doğrulama listesi, gelecek işler |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Tamamlanan işler ve kararlar |
| [docs/calibration/](docs/calibration/README.md) | Kalibrasyon okuma metni ve yöntemi |
