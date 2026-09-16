# Yapı sadeleştirme — Astra, 16 Eylül 2026

## Bulgular

- iFonzo örneğinin özü az görünür kök ve tek belge kaynağıdır (`iFonzo/docs/README.md`); gizli ajan yapılandırmaları orada da vardır. Burada uygulama girişini sırf benzetmek için taşımak gereksizdir.
- Yollar dağınık: çıktı/fallback `dictation.py:222`, log/PID `:47`, SpeechBrain `:1330`, LIVE `:1827`; log saklama sınırsız (`:132`). Envanter: Drive'da 16 MD/0,6 MiB ve 11 kaynak/1003,6 MiB; yerelde log 17,6 MiB, model 84,9 MiB, venv 2831,3 MiB. Yalnız metadata okundu.
- Başlangıç belgesi gerçekle uyuşmuyor: Startup'taki `start.vbs` kopyası doğrudan sabit repo yolunda `pythonw.exe` çalıştırıyor; `docs/auto-start.md:12` BAT zinciri tarif ediyor. `requirements.txt:1` ve `scripts/setup.*` GUI bağımlılıklarını (pystray/Pillow/rumps) kurmuyor; temiz cihaz kurulumu eksik.
- 1147 izlenen `_bmad` dosyasına iki skill ağacı doğrudan bağlı (`.claude/skills/bmad-dev/SKILL.md:9`, `.agents/skills/bmad-dev/SKILL.md:9`). `file_queue.py` ve testi izlenmiyor; ana uygulamada kuyruk bağlantısı yok. `calibration/README.md` henüz yazılmamış `--calibrate` akışını tarif ediyor.

## Öneri

```text
VoiceDictation/
├─ dictation.py, file_queue.py, requirements.txt, LICENSE
├─ README.md, CLAUDE.md          # Kullanıma giriş ve kalıcı ajan kuralları.
├─ docs/                        # Tek belge merkezi: README, TODO, auto-start.
│  ├─ changelog/                # Günlük tamamlanan iş kayıtları.
│  ├─ sessions/                 # Tarihli karar ve inceleme paketleri.
│  └─ arsiv/                    # Eski tarihçe, kalibrasyon ve miras talimatlar.
├─ tools/                       # setup/start betikleri ve Mac launcher üretimi.
├─ tests/                       # Korunan otomatik testler.
├─ data/                        # Git dışında, yedeklenen kullanıcı verisi.
│  ├─ girdi/                    # Kullanıcının elle bıraktığı ses/video dosyaları.
│  ├─ transkript/               # Nihai Markdown çıktıları.
│  └─ ses/                      # Arşivlenen orijinaller ve üretilen WAV'lar.
├─ .local/                      # Git dışında log/PID ve isteğe bağlı model/kuyruk.
├─ venv/                        # Her cihazda yeniden kurulan Python ortamı.
└─ .claude/, .agents/, .codex/   # Araçların beklediği konumda ayarlar ve skill aynası.
```

- **Tek yol noktası:** `dictation.py` başında dosyanın konumundan repo kökü türetilsin; veri/log/model alt yolları buradan gelsin. Yeni ayar dosyası veya veri yolu env override'ı gerekmiyor. Drive/Desktop fallback kalksın; yazılamayan hedef açık hata versin. `.env` kökte, mevcut editör tercihi korunur. LIVE/WAV sistem temp'inde; Whisper platforma özgü varsayılan HF cache'inde kalsın, konumu/yeniden indirme gereği `docs/README.md` içinde yazılsın. SpeechBrain gerekiyorsa `.local/models/`; ortak HF cache topluca taşınmasın veya temizlenmesin.
- **Kullanım:** `girdi/` yalnız dosya bırakma/seçme yeridir, izleyici veya otomatik kuyruk değildir. CLI ve normal dosya akışı orijinali `ses/`e taşımayı; mevcut video akışı orijinali yerinde tutup WAV çıkarmayı sürdürür. Adlar, uzantılar, hotkey, menü ve çıktı biçimi korunur; dış kayıt klasörlerine bağımlılık/referans kaldırılır.
- **Yardımcılar:** `scripts/` → `tools/`; kökteki yerel başlatıcıların görevi burada tekleşsin. Kalibrasyon ve miras talimatlar arşive; `_bmad` ve onu çağıran skill'ler birlikte emekliye ayrılsın, sadece taşınmasın. Ajan dizinleri korunup onaylı senkronla sadeleşsin. `file_queue.py`, `tests/` ve mevcut `.gitignore` değişikliği ayrı, tamamlanmamış iş olarak korunsun; bu düzenleme kuyruğu etkinleştirmesin. Eski diarization çıktıları da merkezi yol kuralına alınmalı (`dictation.py:2923`).
- **Geçiş sırası:** (1) Gelecek uygulama turunda daemon durdurulsun; ad/boyut/çakışma envanteri ve geri dönüş kopyası hazırlansın. (2) Git ignore ve yedek kapsamı tanımlansın. (3) Drive verisi önce kopyalansın; sayı/boyut/hash doğrulanmadan kaynak kaldırılmasın. (4) Yollar, launcher ve tekil belgeler güncellensin; ortak `Records/index.md` yeni konumu göstersin. (5) Windows ve Mac'te dictation, lecture, CLI, video, isim çakışması ve yazma hatası kabulü sonrası eski kopyalar hakkında karar verilsin. Uygulama dosyaları geliştiriciye, veri geçişi ve kabul Yiğit'e aittir.
- **Mac devri:** Kod/belgeler ve `data/` kopyalanır; venv, platform modeli, PID/temp ve launcher yeniden üretilir; yerel ayarlar/sırlar cihazda kurulur. Dört macOS izni ve Mayıs sonrası regresyonlar doğrulanır (`TODO.md:11`). `data/` Git klonuyla gelmez; mevcut rclone filtresi veriyi ve `.local/`ı dahil, `venv/`i hariç tutuyor.

## Riskler / Açık sorular

- `_bmad`/çağırıcı skill'leri emekliye ayırma ve kalibrasyonu arşivleme onaylanıyor mu?
- Eski MD'lerdeki mutlak Kaynak yollarını koruyup yalnız geçiş eşlemesi mi tutalım, yoksa Mac taşınabilirliği için sadece bu alanları göreli yola dönüştürelim mi (`dictation.py:1282`)? İçerik değişmez kararı nedeniyle önerim ilkidir.
- Normal dosya akışının aynı adlı MD üzerine yazmasını bu turda önleyelim mi (`dictation.py:1634`)? Geçiş kopyalaması her durumda çakışmada durmalı.
- Loglar süresiz mi saklanacak; `.local/` içindeki yeniden üretilebilir dosyalar yedekten çıkarılacak mı? Bu tur için otomatik silme önermiyorum.
