# CLAUDE.md — VoiceDictation

Ajan talimatları (Claude Code ve Codex). Projenin ne olduğu, verinin nerede durduğu ve nasıl başlatıldığı [README.md](README.md) dosyasındadır; her oturumda önce onun **Yerel dosyalar** bölümünü oku.

Global kuralların kaynağı `~/.claude/CLAUDE.md` dosyasıdır. `.mcp.json` ve istemci ayarlarını Yiğit yönetir;
sırlar ve kişisel adresler Git'e girmez. Ortak skill'ler projeye kopyalanmaz. Proje skill'i gerekirse kaynak
`.claude/skills/`, üretilen ayna `.agents/skills/` olur; ortak `sync-claude.py --apply`, ardından `--check`
çalıştırılır. Gereksinim olmadan yeni skill veya MCP ekleme. Belge yerleşimi [docs/README.md](docs/README.md) içindedir.

## 1. Mac'te ilk oturum

Mac'te açılan ilk oturumda, ilk yanıtta şunu hatırlat: son Mac doğrulaması 26 Nisan 2026'da yapıldı, sonraki bütün değişiklikler yalnız Windows'ta doğrulandı. Yiğit'e [docs/TODO.md](docs/TODO.md) içindeki "Mac'te ilk oturum" listesini öner.

## 2. Kurallar

- **Commit:** Commit'ten önce Yiğit'in onayını al. `master` dalına yalnız Yiğit push eder; başka bir katkıcı adına çalışıyorsan `feature/<konu>` dalı aç ve PR gönder.
- **Kullanım değişmez:** F13 / Caps Lock x2, "Diktasyon" wake word, tray menüsü, `--transcribe` ve `--aggressive` bayrakları, transkript biçimi. Bunları değiştiren iş yeni özelliktir; ayrı onay ister.
- **Dikte davranışı:** 24 Ekim 2026 son kararı: F13 bitişinde tam sesle tek Whisper çözümlemesi, isteğe bağlı yerel temizlik ve o anda odaktaki alana pano üzerinden tek yapıştırma. Dikte/wake word bitişinde otomatik Enter yoktur. Onaylı Windows istisnası: boşta F13'e 350 ms içinde iki hızlı basış açıkça Enter gönderir; tek basış kayıt açmak için 350 ms bekler, kayıt durdurma anlıktır; işleme sırasında Enter yoktur. Mac Caps Lock değişmez. Canlı dikte önizlemesi, terminal taslağı/rewrite ve Herdr teslimatı geri çekildi; yeniden ekleme ayrı onay ister. **Bağlam kaynağı** yalnız salt okunur ipucudur, teslimat hedefi değildir. Konuşma yalnız doğrulanmış makine/pane/terminal/agent_session kaynağından, user/assistant rol filtresiyle okunur; başka oturum veya en yeni dosya tahmini yapılmaz. İçerik RAM'de kalır; ayrıntılar `docs/mimari.md` içindedir.
- **Veri gizliliği:** `data/` altındaki transkript ve ses dosyalarından, `.local/logs/` içindeki loglardan yalnız ad, boyut ve sayı bilgisini oku. Yiğit istemedikçe içeriklerini okuma veya raporlama.
- **Veri akışı:** Program yalnız `data/media/` (ses + video, girdi ve arşiv aynı klasör) ve `data/raw/` (ham Whisper MD) klasörlerine yazar. `data/transcripts/` elle düzeltilen kopyaların yeridir; oraya yazan kod eklenmez.
- **Daemon:** Çalışıyor olabilir. Yalnız Yiğit'in bilgisiyle durdur (tray → Çıkış). Daemon açıkken `dictation.py`'yi ikinci kez başlatma. `--transcribe` zaten reddedilir (PID kilidi): aynı GPU'da iki model çakışır. Kod değişikliğini `venv\Scripts\python -m py_compile dictation.py` ile denetle.
- **Git temizliği:** Programı kullanmak git durumunu değiştirmez. Çalışma çıktıları yalnız `data/` (değerli) veya `.local/` (yeniden üretilir) altına yazılır; ikisi de ignore'ludur. Yeni bir çıktı türü de bu iki klasörden birine gider.
- **Yollar tek yerde:** Tüm yollar `dictation.py` başındaki yol bloğundadır (`BASE_DIR`, `DATA_DIR`, `MEDIA_DIR`, `RAW_DIR`, `TRANSCRIPTS_DIR`, `LOCAL_DIR`, `_LOG_DIR`, `MODELS_DIR`, `CLEANUP_MODEL`, `CLEANUP_SERVER_BIN`, `CLEANUP_CUDA_SERVER_BIN`, `TIMING_FILE`; eski `CLEANUP_BIN` ve `CLEANUP_TEMP_DIR` kullanılmadan durur). Repo dışına veri yazan kod ekleme.
- **Belge bakımı:** Yol, klasör, menü veya CLI değiştiren commit, aynı commit içinde README'deki "Yerel dosyalar" tablosunu ve [docs/nasil-calisir.md](docs/nasil-calisir.md) dosyasını günceller. Teslimden önce şu komut boş dönmeli:

  ```bash
  grep -n -e "Driv[e]'" -e "Meet Recording[s]" -e "RawRecord[s]" -e "_Lecture[s]" README.md CLAUDE.md dictation.py docs/*.md | grep -v "^docs/CHANGELOG"
  ```

- **İş takibi:** Açık işler [docs/TODO.md](docs/TODO.md) dosyasına, tamamlananlar [docs/CHANGELOG.md](docs/CHANGELOG.md) dosyasına (en yeni üstte) yazılır. Bu dosyada tarihçe tutulmaz.
- **Araştırma kayıtları:** Çok ajanlı analiz ve uygulama turlarının brif ve sonuçları `docs/sessions/YYYY-MM-DD-<konu>/` altında durur.
- **Dil ve üslup:** Yiğit ile Türkçe konuş. Kod yorumlarını mevcut üsluba uyarak ASCII Türkçe yaz. Kütüphane API'sinden emin değilsen önce Context7 ile doğrula.

## 3. Mimari özeti

- **Modüller:** Ana uygulama `dictation.py`; `context_bridge.py` yalnız tam oturum ID/yol çözümleme ve rol/sınır filtresi; `context_source.py` yerel/SSH kaynak doğrulama ve RAM önbelleğidir. `remote_dictation.py` Vault (iPhone/iPad) uzak dikte ucudur: yalnız `127.0.0.1:5190`, yapıştırmasız, metni yanıtla döndürür. Durum makinesi `LISTENING → RECORDING → PROCESSING → COOLDOWN` (mutex korumalı). Ayrı mod ekseni: dikte ↔ toplantı (lecture).
- **Ses yolu:** sounddevice → numpy tamponu → tek Whisper → isteğe bağlı yerel temizlik → pano → pynput ile o an odaktaki alana yapıştır. Dikte bitişinde otomatik Enter ve Herdr teslimatı yoktur; Windows boşta F13 çift basış ayrı Enter hareketidir.
- **STT:** Windows'ta faster-whisper (CUDA, yoksa CPU), macOS'ta mlx-whisper (Silero VAD ön filtresiyle). Model: turbo. Dikte `beam=3`, toplantı ve dosya transkripti `beam=5`.
- **Arayüz:** Windows'ta pystray tepsi simgesi, macOS'ta rumps menü çubuğu. Durum renkleri: yeşil hazır, kırmızı kayıt, sarı işleniyor, mor toplantı.
- **Kapalı kodlar:** Konuşmacı ayırma (speechbrain) kodu duruyor ama tray'den çağrılmıyor. `file_queue.py` dış istemci kuyruğudur, daemon'a bağlı değil. Testler: `venv\Scripts\python -m unittest discover -s tests`.

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
