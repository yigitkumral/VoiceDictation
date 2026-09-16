# Sonuç — opus-ortam (çalışma ortamı, yerel bağımlılıklar, taşınabilirlik) · 16 Eylül 2026

## Bulgular

- **Kurulum bugünkü ortamı üretemiyor.** `requirements.txt` yalnız 5 paket içeriyor. Tepsi için gereken `pystray` + `Pillow` (`dictation.py:579-580`) ile Mac'in `rumps`'ı (`:450`) listede yok: temiz kurulumda uygulama tepsi/menü çubuğu açılırken çöker. `mlx-whisper` yalnız `scripts/setup.sh:22`, `nvidia-*` yalnız `setup.bat:16` içinde ve sürümleri sabitlenmemiş. Mac'te de `faster-whisper` gerekiyor (VAD için, `:898`).
- **venv içeriği:** venv Python 3.14.2 ile kurulmuş (`venv/pyvenv.cfg`), README ise "3.10+" diyor (`README.md:28`). 2,8 GB'ın 1,7 GB'ı `nvidia/`. Diarize paketleri (`speechbrain`, `torch`, `scikit-learn`, ~700 MB) kurulu ama listede yok. `ImageHash` ve `imageio_ffmpeg` hiçbir yerde kullanılmıyor. CUDA DLL yolu venv'i `<repo>/venv` konumunda arıyor (`:147-156`), bu yüzden venv'in adı ve yeri değişmemeli.
- **Modeller:** Kod, indirme klasörü vermeden modeli adıyla yüklüyor: `WhisperModel("turbo")` (`:752`) ve Mac'te `mlx-community/whisper-turbo` (`:749`). Bu yüzden modeller HF önbelleğine iniyor.
  - HF önbelleği başka projelerle ortak: Qwen 7,6 GB, gliner 2,2 GB, bert 0,4 GB.
  - Kodda karşılığı olmayan Whisper modelleri: `large-v3` (2,9 GB, son değişiklik 15 Eylül 22:05), `medium` ve `small` (1,9 GB, 14 Mart).
  - `iFonzo/tools/voice/` altındaki dosyalarda bu model adları geçiyor (yalnız dosya adı eşleşmesine baktım, içeriği okumadım).
  - speechbrain modelinin iki kopyası var. Bu tasarımdan kaynaklanıyor: kod modeli önbellekten `models/` altına kopyalıyor (`LocalStrategy.COPY`, `:1330-1340`). Ek yük 85 MB.
- **Loglar kişisel metin arşivi gibi çalışıyor.** Dosya sayısına sınır yok (`backupCount=0`, `:127-131`): 157 dosya, ~18 MB, 19 Mart'tan bugüne.
  - Her diktasyonun tam metni INFO seviyesinde loglanıyor: `[OK] >> {msg}` (`:3198`) ve `[CHECK] Duydum: {text}` (`:3262`).
  - Canlı kayıtta her cümlenin ilk 80 karakteri loglanıyor (`:1795`).
  - Bu loglar rclone ile Drive'a yedekleniyor. Oysa `file_queue.py:8` "transkript metni log'a yazılmaz" diyor, yani iki politika çelişiyor.
  - Kökteki `dictation.log` (17 Mart, 680 KB) artık yazılmayan eski bir dosya. PID dosyası `logs/dictation.pid` (`:50`).
- **Geçici dosyalar temizleniyor:** Mac ses dosyası `:338-342`, afconvert çıktısı `:1131-1133`. LIVE klasörü sistem temp'inde (`:1827`) ve şu an boş.
- **Başlatma tek kaynaklı değil.**
  - Windows: Startup klasöründeki `start.vbs`, kökteki gitignore'lu dosyanın birebir **kopyası**. Yolu sabit yazılmış ve `pythonw.exe`'yi doğrudan çalıştırıyor.
  - Kökteki `start.bat` hiç kullanılmıyor. `scripts/start.bat` ise konsollu `python -u` açıyor. Toplam üç farklı başlatıcı var.
  - `docs/auto-start.md` ve `CLAUDE.md §1` "vbs, start.bat'i çalıştırır" ve "kısayol" diyor. İkisi de yanlış.
  - Mac: `.app` içindeki `main.scpt` şu yolu sabit içeriyor: `cd '/Users/yigitkumral/Desktop/Yazılım/VoiceDictation'`. Mac'te klasör adı `Yazılım`, Windows'ta `Yazilim`.
- **Sırlar ve yapılandırma:**
  - `.env` yok. `_get_hf_token` (`:119`) hiçbir yerden çağrılmıyor, yani HF token şu an gereksiz.
  - `.codex/config.toml` **git'te izleniyor** ve Windows'a sabit yollar içeriyor (`C:\Python314\python.exe`, `…\iFonzo\docs\tools-global\codex\sync-claude.py`). Mac'te çalışmaz.
  - `.mcp.json` gitignore'da ama içinde sabit Windows yolu var. `.claude/settings.local.json` gitignore'da, içinde sır yok.
  - `.gitignore:29`'daki `settings.json` kuralı köke bağlı değil, her klasördeki `settings.json`'ı gizliyor.
- **Yedek:** Filtre `venv/`, `__pycache__/`, `.cache/` ve `.playwright-mcp/` klasörlerini dışarıda bırakıyor; `logs/`, `models/` ve `.local/` yedeğe giriyor. rclone yalnız değişen dosyaları yüklüyor. Mevcut ~1 GB ses bir kez gider; sonrasında her saatlik toplantı ~115 MB WAV ekler (16 kHz, mono, 16 bit).

## Öneri

1. **Git dışında iki kök klasör olsun: `data/` değerli, `.local/` makineye özel.** Alt klasör adları, yapı/yol ajanlarının önerisine göre belirlenir.
   ```
   VoiceDictation/
   ├── dictation.py · file_queue.py · requirements.txt · README.md · CLAUDE.md
   ├── scripts/   setup.bat · setup.sh · start.vbs (tek, göreli) · start.sh · VoiceDictation.app
   ├── docs/ · tests/ · calibration/
   ├── data/      git dışı · YEDEKLENİR · yeni cihaza KOPYALANIR   (girdi / transkript / ses)
   ├── .local/    git dışı · yedeklenmez · yeniden üretilir
   │   ├── logs/  (+ dictation.pid)   ├── models/  (speechbrain)   └── file-queue/
   └── venv/      git dışı · yedeklenmez · platforma özel (yeri değişmez)
   ```
2. **Tek `requirements.txt`, platforma göre koşullu satırlarla (PEP 508):** Windows'a `pystray`, `Pillow`, `nvidia-cublas-cu12`, `nvidia-cudnn-cu12`; Mac'e `rumps`, `mlx-whisper`. Kurulum betikleri "venv oluştur + `pip install -r`" düzeyine iner. Diarize paketleri yorum satırında "opsiyonel" olarak durur. README'ye denenen Python sürümü yazılır.
3. **Modeller kullanıcı önbelleğinde kalsın.** `HF_HOME` ve `download_root` değiştirilmesin, çünkü önbellek başka projelerle ortak ve Mac zaten farklı bir model reposu kullanıyor. Bunun yerine modelin yeri belgelensin. speechbrain modelinin kaydedildiği klasör `.local/models/` olsun.
4. **Loglar `.local/logs/` altına taşınsın ve `backupCount=30` olsun.** Tam metin yazan satırlar (`:3198`, `:3262`, `:1795`) yalnız karakter sayısı yazacak şekilde değiştirilsin; böylece `file_queue` politikasıyla aynı olur (soru 6).
5. **Başlatma için tek kaynak:**
   - Windows: git'te izlenen `scripts/start.vbs` repo kökünü kendi konumundan bulsun. Startup klasörüne kopya yerine **kısayol** konsun; kısayolu `setup.bat` oluştursun. Kökteki `start.bat`/`start.vbs` ve ilgili gitignore satırları kaldırılsın.
   - Mac: `main.scpt`, sabit yol yerine `path to me` ile kendi konumundan yolu bulsun.
6. **Yedek filtresi:** Filtreye `- /VoiceDictation/.local/` eklensin. Geçiş süresince `logs/` ve `models/` kuralları da eklenebilir. `data/` yedekte kalsın; taşıma bitince Drive'daki `Records/` kaldırılırsa çift kopya da biter.
7. **Belgeler tek yerde toplansın (iFonzo'daki gibi):**
   - `README.md` iki bölüm alsın: "Kurulum ve yeni cihaz" ile "Yerel dosyalar" tablosu (yol · ne · git · yedek · yeni cihazda).
   - Tabloya sistem temp'teki LIVE dosyası ve HF önbelleği de girsin.
   - `docs/auto-start.md` bu bölümlere katılsın. CLAUDE.md §0.5 ile TODO'daki "Mac'te ilk session" listesi bu bölüme bağlantı versin.
8. **MacBook kontrol listesi:**
   - **Kopyalanacak:** yalnız `data/`.
   - **Yeniden üretilecek:**
     1. `git pull`, ardından `scripts/setup.sh`.
     2. İlk çalıştırmada MLX turbo modeli iner (~1,6 GB).
     3. `.mcp.json` `.example` dosyasından üretilir; `.codex/config.toml` `sync-claude.py` ile üretilir (bu dosya gitignore'a alınmalı).
     4. `.app` Login Items'a eklenir ve 4 TCC izni verilir.
     5. TODO'daki doğrulama listesi uygulanır. Veri artık repo içinde olacağı için "Drive yolu" maddesi düşer.
   - **Kopyalanmayacak:** `.env` (yok), `venv`, `.local`.

## Riskler / Açık sorular

1. Taşıma tek yönlü mü, yoksa Windows ve Mac paralel mi kullanılacak? Paralel kullanılırsa `data/` iki cihazda ayrışır, çünkü bugün eşitlemeyi Drive'daki `Records/` yapıyor.
2. Mac'te `Yazilim` klasörü yedekleniyor mu? Yedeklenmiyorsa Mac'teki `data/` tek kopya kalır.
3. Mac'teki `Yazılım` klasörü ASCII `Yazilim` olarak yeniden adlandırılsın mı? Adlandırılırsa `.app` yeniden derlenip imzalanmalı; bu durumda TCC izinleri sıfırlanabilir.
4. Kodda karşılığı olmayan `medium` + `small` modelleri (1,9 GB) silinsin mi? `large-v3` (2,9 GB) iFonzo'nun `tools/voice` aracına mı ait? Silmeden önce iFonzo tarafında doğrulanmalı.
5. Diarize kapalıyken `speechbrain`/`torch`/`scikit-learn` (~700 MB) ve kullanılmayan `ImageHash`/`imageio_ffmpeg` kurulu kalsın mı? venv sıfırdan mı kurulsun?
6. Loglarda tam diktasyon metni kalsın mı, saklama süresi ne olsun? Mevcut 157 log dosyası ve kökteki eski `dictation.log` silinsin mi, arşivlensin mi?
7. `.local/` (loglar dahil) yedekten tamamen çıkarılsın mı?
8. `.codex/config.toml` git'te izlenmeye devam etsin mi? Windows yolları içerdiği için Mac'te her `git pull` ile uyuşmazlık çıkar.
