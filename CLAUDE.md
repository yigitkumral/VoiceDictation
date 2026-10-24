# CLAUDE.md — VoiceDictation

Ajan talimatları (Claude Code ve Codex). Projenin ne olduğu, verinin nerede durduğu ve nasıl başlatıldığı [README.md](README.md) dosyasındadır; her oturumda önce onun **Yerel dosyalar** bölümünü oku.

Global kuralların kaynağı `~/.claude/CLAUDE.md` dosyasıdır. `.mcp.json` ve istemci ayarlarını Yiğit yönetir;
sırlar ve kişisel adresler Git'e girmez. Ortak skill'ler projeye kopyalanmaz. Proje skill'i gerekirse kaynak
`.claude/skills/`, üretilen ayna `.agents/skills/` olur; ortak `sync-claude.py --apply`, ardından `--check`
çalıştırılır. Gereksinim olmadan yeni skill veya MCP ekleme. Belge yerleşimi [docs/README.md](docs/README.md) içindedir.

## 1. Mac'te ilk oturum

Son Mac doğrulaması 25 Ekim 2026: yeni `dev/` ve `.local/` yerleşiminde 187 Python testi ve 12 trackpad senaryosu geçti. Mikrofon izni verildi; yeni başlatıcının klavye izinleri ve gerçek kullanım kabulü [docs/TODO.md](docs/TODO.md) içinde takip edilir. Önceki ortam `.local/migration-20261025/` altında kabul tamamlanana kadar korunur.

## 2. Kurallar

- **Commit:** Commit'ten önce Yiğit'in onayını al. `master` dalına yalnız Yiğit push eder; başka bir katkıcı adına çalışıyorsan `feature/<konu>` dalı aç ve PR gönder.
- **Kullanım değişmez:** F13 / Caps Lock x2, "Diktasyon" wake word, tray menüsü, `--transcribe` ve `--aggressive` bayrakları, transkript biçimi. Bunları değiştiren iş yeni özelliktir; ayrı onay ister.
- **Dikte davranışı:** 24 Ekim 2026 son kararı: F13 bitişinde tam sesle tek Whisper çözümlemesi, isteğe bağlı yerel temizlik ve o anda odaktaki alana pano üzerinden tek yapıştırma. Dikte/wake word bitişinde otomatik Enter yoktur. F13'e ilk basışta sessiz aday kayıt başlar; bırakıştan sonra 250 ms içinde ikinci basış gelirse aday atılır ve Enter gönderilir, aksi halde başlangıç tonu çalar. Kayıt durdurma anlıktır; işleme sırasında Enter yoktur. Mac Caps Lock değişmez; onaylı trackpad prototipi için Mac'te ayrıca aynı F13 yolu açılmıştır. `dev/mac_trackpad.py` ve `dev/mac-trackpad/` yerel modülü aynı daemon sürecinde çalışır; modül varsa açık başlar ve Ayarlar menüsünden kapatılır. Ayrı TP uygulaması kullanılmaz. Özel Apple API'si kullanılır; ses ve fiziksel hareket kabulü sürer. Canlı dikte önizlemesi ve terminal taslağı/rewrite geri çekildi. **Bağlam kaynağı** salt okunur ipucudur; masaüstünde teslimat hedefi değildir. Konuşma yalnız doğrulanmış makine/pane/terminal/agent_session kaynağından, user/assistant rol filtresiyle okunur; başka oturum veya en yeni dosya tahmini yapılmaz. Ayrıntılı tanı kullanıcı onayıyla `.local/diagnostics/` altında tutulur; ayrıntılar `docs/mimari.md` ve `docs/nasil-calisir.md` içindedir.
- **Veri gizliliği:** `.local/data/` altındaki transkript ve ses dosyalarından, `.local/logs/` içindeki loglardan yalnız ad, boyut ve sayı bilgisini oku. Yiğit istemedikçe içeriklerini okuma veya raporlama.
- **Veri akışı:** Program yalnız `.local/data/media/` (ses + video, girdi ve arşiv aynı klasör) ve `.local/data/raw/` (ham Whisper MD) klasörlerine yazar. `.local/data/transcripts/` elle düzeltilen kopyaların yeridir; oraya yazan kod eklenmez.
- **Daemon:** Çalışıyor olabilir. Yalnız Yiğit'in bilgisiyle durdur (tray → Çıkış). Daemon açıkken `dev/dictation.py`'yi ikinci kez başlatma. `--transcribe` zaten reddedilir (PID kilidi): aynı GPU'da iki model çakışır. Kod değişikliğini `.local\venv\Scripts\python -m py_compile dev/dictation.py` ile denetle.
- **Git temizliği:** Programı kullanmak git durumunu değiştirmez. Bütün yerel dosyalar Git dışı `.local/` altındadır. `.local/data/` değerli kayıtları içerir; `.local/` bütünüyle silinebilir önbellek değildir. Yeni çalışma çıktısı bu ağaca gider.
- **Yollar tek yerde:** Tüm yollar `dev/dictation.py` başındaki yol bloğundadır (`BASE_DIR`, `SOURCE_DIR`, `DATA_DIR`, `MEDIA_DIR`, `RAW_DIR`, `TRANSCRIPTS_DIR`, `LOCAL_DIR`, `_LOG_DIR`, `MODELS_DIR`, `CLEANUP_MODEL`, `CLEANUP_SERVER_BIN`, `CLEANUP_CUDA_SERVER_BIN`, `TIMING_FILE`). `.env` yalnız `.local/.env` konumundan yüklenir. Repo dışına veri yazan kod ekleme.
- **Belge bakımı:** Yol, klasör, menü veya CLI değiştiren commit, aynı commit içinde README'deki "Yerel dosyalar" tablosunu ve [docs/nasil-calisir.md](docs/nasil-calisir.md) dosyasını günceller. Teslimden önce şu komut boş dönmeli:

  ```bash
  grep -n -e "Driv[e]'" -e "Meet Recording[s]" -e "RawRecord[s]" -e "_Lecture[s]" README.md CLAUDE.md dev/dictation.py docs/*.md | grep -v "^docs/CHANGELOG"
  ```

- **İş takibi:** Açık işler [docs/TODO.md](docs/TODO.md) dosyasına, tamamlananlar [docs/CHANGELOG.md](docs/CHANGELOG.md) dosyasına (en yeni üstte) yazılır. Bu dosyada tarihçe tutulmaz.
- **Araştırma kayıtları:** Çok ajanlı analiz ve uygulama turlarının brif ve sonuçları `docs/sessions/YYYY-MM-DD-<konu>/` altında durur.
- **Dil ve üslup:** Yiğit ile Türkçe konuş. Kod yorumlarını mevcut üsluba uyarak ASCII Türkçe yaz. Kütüphane API'sinden emin değilsen önce Context7 ile doğrula.

## 3. Mimari özeti

- **Modüller:** Ana uygulama `dev/dictation.py`; `dev/context_bridge.py` yalnız tam oturum ID/yol çözümleme ve rol/sınır filtresi; `dev/context_source.py` yerel/SSH kaynak doğrulama ve RAM önbelleğidir. `dev/remote_dictation.py` Vault (iPhone/iPad) uzak dikte ucudur: yalnız `127.0.0.1:5190`, yapıştırmasız, metni yanıtla döndürür. `dev/diagnostics.py`, `DIAGNOSTIC_DIR` altında izinli ayrıntılı kayıtları arka planda yazar; `dev/scripts/compare-dictation.py` karşılaştırır. Durum makinesi `LISTENING → RECORDING → PROCESSING → COOLDOWN` (mutex korumalı). Ayrı mod ekseni: dikte ↔ toplantı (lecture).
- **Ses yolu:** sounddevice → numpy tamponu → tek Whisper → isteğe bağlı yerel temizlik → pano → pynput ile o an odaktaki alana yapıştır. Dikte bitişinde otomatik Enter ve Herdr teslimatı yoktur; Windows boşta F13 çift basış ayrı Enter hareketidir.
- **STT:** Windows'ta faster-whisper (CUDA, yoksa CPU), macOS'ta mlx-whisper (Silero VAD ön filtresiyle). Model: turbo. Dikte `beam=3`, toplantı ve dosya transkripti `beam=5`.
- **Arayüz:** Windows'ta pystray tepsi simgesi, macOS'ta rumps menü çubuğu. Durum renkleri: yeşil hazır, kırmızı kayıt, sarı işleniyor, mor toplantı.
- **Kapalı kodlar:** Konuşmacı ayırma (speechbrain) kodu duruyor ama tray'den çağrılmıyor. `dev/file_queue.py` dış istemci kuyruğudur, daemon'a bağlı değil. Testler: `.local\venv\Scripts\python -m unittest discover -s dev/tests`.

## 4. Belge haritası

| Belge | Görevi |
|---|---|
| [README.md](README.md) | İnsan girişi, kurulum özeti, kullanım, **yerel dosyalar tablosu** |
| [docs/mimari.md](docs/mimari.md) | Güncel mimari, bağlam kaynağı ve yapıştırma ayrımı |
| [docs/nasil-calisir.md](docs/nasil-calisir.md) | Mod akışları, tray menüsü, çıktı biçimi, halüsinasyon katmanları, ayarlar |
| [docs/kurulum.md](docs/kurulum.md) | Kurulum, otomatik başlatma, macOS izinleri, yeni cihaza taşıma |
| [docs/TODO.md](docs/TODO.md) | Açık işler, Mac doğrulama listesi, gelecek işler |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Tamamlanan işler ve kararlar |
| [docs/calibration/](docs/calibration/README.md) | Kalibrasyon okuma metni ve yöntemi |
