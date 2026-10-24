# VoiceDictation

Yerel Whisper modeliyle çalışan, Windows ve macOS'ta kullanılan sesli yazım aracı. F13 / Caps Lock x2 ile kaydı başlatıp bitirirsin; kayıt tamamlanınca Whisper bir kez çalışır, isteğe bağlı yerel temizlik uygulanır ve metin o anda odaktaki alana pano üzerinden yapıştırılır. **Dikte sonunda otomatik Enter gönderilmez.** Windows'ta boşta F13'e iki hızlı basış ayrı bir Enter hareketidir. Toplantı ve ders kayıtlarını Markdown transkriptlerine, ses ve video dosyalarını da yüksek kaliteli transkriptlere dönüştürür. Ses makineden çıkmaz.

> **Türkçe için özelleştirildi.** Whisper `language="tr"` ile çalışır. Kelime listesi (`INITIAL_PROMPT`), halüsinasyon filtreleri ve "Diktasyon" wake word varyasyonları Türkçe çıktılara göre yazıldı. Arayüz, log ve yorumlar Türkçedir; başka dil için kod uyarlaması gerekir.

## Özellikler

- **Tek sefer dikte:** F13 (Windows) veya Caps Lock x2 (macOS) ile kayıt aç/kapat; bitişte tek çözümleme ve tek yapıştırma. Windows'ta ilk F13 basıldığı anda ses kaydı başlar. Tuş bırakıldıktan sonra yalnız başlangıç tonu 250 ms bekler; hızlı çift basış gelirse kısa kayıt sessizce atılır ve Enter gönderilir. Tonu beklemeden konuşabilirsin. Kesinleşmiş kaydı durdurma anlıktır; işleme sırasında Enter gönderilmez. Canlı dikte önizlemesi veya terminal taslağı yoktur.
- **Konuşma bağlamı:** Doğrulanmış Herdr kaynağındaki son kullanıcı/asistan konuşmasından en fazla 300 kelime RAM'de tutulur; Whisper'a en fazla 160 token konuşma + 40 token terim verilir. Tekil tam pencere başlığı eşleşmesi yoksa **Bağlam kaynağı** menüsünden seçim gerekir. Bu seçim yapıştırmayı yönlendirmez; ayrıntılar [mimari şemasında](docs/mimari.md).
- **Uzak dikte (iPhone/iPad, Windows sunucu):** iFonzo canlı ajan grafının (Vault) kart terminalindeki mikrofon düğmesi sesi tailnet üzerinden bu daemon'a yollar. Ses aynı Whisper ve temizlikle çözülür; metin terminale Enter olmadan yazılır, pano kullanılmaz. Uç yalnız `127.0.0.1:5190`'da dinler, Vault'un köprüsü aracılık eder; ses diske yazılmaz. Ayrıntı [mimari şemasında](docs/mimari.md).
- **Yerel temizlik:** Model ve çalıştırıcı mevcutsa başlangıçta açıktır, eksikse kapalıdır; tray'den kapatılabilir. Qwen arka plandaki yerel `llama-server` alt sürecinde bellekte tutulur; hazır değilse beklenmeden Whisper metni kullanılır. 1200 karakter ve 12 saniye sınırı, sayı/ad/teknik yazım koruması geçerlidir.
- **Süre ölçümü:** Tray son diktenin süre özetini gösterir. Bağlam bekleme, Whisper, temizlik, yapıştırma ve F13 bitişinden yapıştırmaya toplam süre `.local/metrics/dictation.jsonl` içinde metin/pencere/pane adı olmadan tutulur.
- **Wake word:** "Diktasyon" diyerek başlat ve bitir (varsayılan kapalı, tray'den açılır).
- **Toplantı modu:** Uzun kayıtta canlı transkript editörde akar; kayıt bitince sesi WAV olarak saklar ve yüksek kaliteli son transkripti yazar.
- **Dosyadan transkript:** AAC, MP3, WAV, M4A, iPhone `.qta` ve MP4 gibi video dosyaları dahil; tray'den veya `--transcribe` ile.
- **GPU:** Windows'ta Whisper CUDA (yoksa CPU), macOS'ta Apple Silicon üzerinde MLX. Windows Qwen temizliği aynı modelle CUDA'da çalışır; uygun aygıt yoksa veya GPU sunucusu hata verirse CPU yedeğine geçer. Menü GPU/CPU hazır durumunu gösterir; ölçümler [oturum kaydındadır](docs/sessions/2026-10-24-gpu-double-tap/README.md).

## Kurulum

Python 3.12 veya üstü gerekir (3.14.2 ile test edildi). Tüm bağımlılıklar tek `requirements.txt` içindedir; platforma özel paketler (Windows: `pystray`, `Pillow`, CUDA kütüphaneleri; macOS: `rumps`, `mlx-whisper`) kendiliğinden seçilir.

```bash
git clone https://github.com/yigitkumral/VoiceDictation.git
cd VoiceDictation
scripts\setup.bat          # Windows: venv + paketler + açılışta başlatma kısayolu
./scripts/setup.sh         # macOS: portaudio + venv + paketler
```

Ayrıntılar, otomatik başlatma, macOS izinleri ve yeni cihaza taşıma: [docs/kurulum.md](docs/kurulum.md).

## Başlatma

| Platform | Arka planda (normal kullanım) | Konsollu (hata ayıklama) |
|---|---|---|
| Windows | `scripts\start.vbs` — açılışta Startup kısayolu çalıştırır | `scripts\start.bat` |
| macOS | `scripts/VoiceDictation.app` — Login Items çalıştırır | `./scripts/start.sh` veya `venv/bin/python dictation.py` |

Uygulama her zaman repodaki güncel `dictation.py`'yi çalıştırır; `git pull` sonrası bir sonraki açılışta yeni kod devrededir. Aynı anda tek örnek çalışır (PID kilidi). Kapatmak için: tray / menü çubuğu → **Çıkış**.

## Kullanım

| İşlem | Windows | macOS |
|---|---|---|
| Kaydı başlat / bitir ve metni yaz | F13 | Caps Lock iki kez |
| Boştayken açıkça Enter gönder | F13 iki hızlı basış (250 ms içinde) | Yok; Caps Lock davranışı değişmez |
| Sesle başlat / bitir | "Diktasyon" | "Diktasyon" |
| Kaydı iptal et | F13'ü 1,25 sn basılı tut | Caps Lock üç kez |
| Toplantı kaydı, dosya dökme, Meet Dictation | Tray → 🎤 Toplantı | Menü çubuğu → 🎤 Toplantı |

Dosya seçiciler `data/media/` klasöründe açılır: işlenecek ses veya video dosyasını önce oraya bırak. Aynı klasör programın yazdığı WAV'ları da tutar, yani girdi ve arşiv tek yerdedir. Daemon kapalıyken komut satırından da çevirebilirsin:

```bash
venv\Scripts\python dictation.py --transcribe "data\media\kayit.m4a"     # Windows
venv/bin/python dictation.py --transcribe "data/media/kayit.qta"         # macOS
```

Modların adım adım akışı, tray menüsü, çıktı biçimi ve ayarlar: [docs/nasil-calisir.md](docs/nasil-calisir.md).

## Yerel dosyalar

Git yalnız kodu ve belgeleri taşır. Aşağıdaki tablo projenin makinede tuttuğu her şeyin **tek** listesidir; yol veya klasör değişirse önce burası güncellenir.

| Yol | İçerik | Sınıf | Yeni cihazda |
|---|---|---|---|
| `data/media/` | **Ses ve video dosyalarının tek klasörü.** Elle bırakılan kayıtlar (Meet `.mp4`, iPhone `.m4a`/`.qta`, …) ve programın yazdığı WAV'lar birlikte durur; dosya seçiciler burada açılır. Dışarıdan `--transcribe` ile verilen dosya buraya taşınır, zaten buradaysa yerinde kalır. | Değerli, git dışı | Kopyalanır |
| `data/raw/` | **Programın tek Markdown çıktısı:** Whisper'ın düzeltilmemiş ham transkriptleri. Her akış (toplantı, dök, Meet) buraya yazar. | Değerli, git dışı | Kopyalanır |
| `data/transcripts/` | **Elle düzeltilmiş transkriptler.** `data/raw/` içindeki dosya aynı adla buraya kopyalanır ve düzeltme burada yapılır. Program bu klasöre yazmaz, yalnız oluşturur. | Değerli, git dışı | Kopyalanır |
| `.local/logs/` | Aylık log (`YYYY-MM-<Ay>.log`, örn. `2026-09-Eylul.log`; dikte metni dahil tam içerik, silinmez) ve `dictation.pid` | Makineye özel, git dışı | Kendiliğinden oluşur |
| `.local/models/` | speechbrain modeli (uyuyan özellik); isteğe bağlı `Qwen3-1.7B-Q8_0.gguf` metin temizleme modeli | Makineye özel, git dışı | Qwen ayrı onayla elle indirilir; uygulama indirmez |
| `.local/llama/` | Yerel temizlik için llama.cpp `llama-server` çalıştırıcısı ve kitaplıkları | Makineye özel, git dışı | Platforma uygun sürüm elle kurulur |
| `.local/llama-macos-dist/`, `.local/llama-b11852-bin-macos-arm64.tar.gz` | Apple Silicon için resmi b11852 çalıştırıcısı ve arşivi; Mac'te `.local/llama` bu dağıtıma bağlıdır. Qwen modeli Windows'taki onaylı kopyadan taşınır. | Makineye özel, git dışı | Mac dağıtımı kurulmalı; Windows ikilisi kullanılamaz |
| `.local/llama-cuda/` | Aynı Qwen modeli için onaylı llama.cpp b11852 CUDA 13.4 çalıştırıcısı ve çalışma zamanı; CPU yedeği `.local/llama/` altındadır | Makineye özel, git dışı | Platforma uygun onaylı kurulum gerekir |
| `.local/cleanup-temp/` | Önceki süreç-başına temizlik sürümünün geçici girdi klasörü; kalıcı model akışı kullanmaz, eski çökmeden kalan dosya bulunabilir | Makineye özel, git dışı | Taşımak gerekmez |
| `.local/metrics/dictation.jsonl` | Yalnız dikte süreleri, uzunluklar ve durum; dikte metni, pencere/pane adı içermez | Makineye özel, git dışı | Kendiliğinden oluşur |
| `.local/diagnostics/YYYY-MM-DD.jsonl` | Yiğit'in onayıyla masaüstü/Vault dikte ve Enter tanısı: kullanım yolu, bildirilen cihaz türü, tarayıcı ve istek kimliği; kaynak pencere/pane/sohbet kimliği, kullanılan bağlam ve model promptları, ham/filtreli/aday/seçilmiş metin, hedef bilgisi, süreler ve kod sürüm özeti. Ses veya API anahtarı içermez. | Kişisel içerik taşıyabilir, git dışı | Yeni kullanımda oluşur; eski olaylar geriye dönük tamamlanmaz |
| `.local/llama-b11852-bin-win-cuda-13.4-x64.zip`, `.local/cudart-llama-bin-win-cuda-13.4-x64.zip`, `.local/llama-cuda-download.json` | Onaylı resmi CUDA çalıştırıcısı/çalışma zamanı arşivleri ve doğrulanmış indirme/hash kaydı | Makineye özel, git dışı | Yeniden kurulumda oluşturulabilir |
| `.local/cleanup-gpu-evaluation.json` | GPU temizlik sentetik kalite/gecikme ölçüm kaydı; çalışma için gerekmez | Makineye özel, git dışı | Gerektiğinde yeniden üretilir |
| `.local/cleanup-v3-evaluation.json` | Yerel temizlik için sentetik kalite/gecikme ölçüm kaydı; çalışma için gerekmez | Makineye özel, git dışı | Gerektiğinde yeniden üretilir |
| `.local/rejected-prototypes/` | Geri çekilen canlı dikte/terminal deneylerinin eski test arşivi; aktif akış kullanmaz | Makineye özel, git dışı | Taşımak gerekmez |
| `.local/llama-b11852.zip`, `.local/model-download.json` | Onaylı kurulumun arşivi ve model sürüm/hash kaydı | Makineye özel, git dışı | Yeniden kurulumda oluşturulabilir |
| `.local/file-queue/` | `file_queue.py` iş kuyruğu (daemon'a bağlı değil) | Makineye özel, git dışı | Kendiliğinden oluşur |
| `venv/` | Python ortamı | Platforma özel, git dışı | `scripts/setup.*` ile kurulur |
| `.env` | İsteğe bağlı ortam değişkenleri (aşağıda); bugün kullanılmıyor | Makineye özel, git dışı | Gerekirse elle oluşturulur |
| `~/.cache/huggingface/hub/` | Whisper turbo modeli (Windows: `mobiuslabsgmbh/faster-whisper-large-v3-turbo`, macOS: `mlx-community/whisper-turbo`). Önbellek başka projelerle ortaktır; buradaki diğer modeller silinmez. | Repo dışı | İlk açılışta iner |
| Sistem temp → `voicedictation_live/` | Toplantı sırasında canlı `LIVE.md` ve geçici WAV | Repo dışı, geçici | Kendiliğinden oluşur, kayıt bitince silinir |
| Windows Startup → `VoiceDictation.lnk` | `scripts\start.vbs` kısayolu | Repo dışı | `scripts\setup.bat` oluşturur |
| macOS Login Items → `VoiceDictation` | `scripts/VoiceDictation.app` | Repo dışı | Elle eklenir ([kurulum](docs/kurulum.md)) |

**Yeni cihaza taşıma özeti:** Yalnız `data/` kopyalanır. Geri kalan her şey kurulumla ya da ilk çalıştırmada yeniden oluşur. Cihazlar arasında veri eşitlemesi yoktur.

`data/` ile `.local/` klasörleri program ilk açıldığında oluşur. Programı kullanmak git durumunu değiştirmez.

Yerel temizlik model ve çalıştırıcı mevcutsa açık başlar; Ayarlar ve Windows'taki Bağlam kaynağı seçimleri yalnız o çalıştırma boyunca geçerlidir. Yeni ayar dosyası yazılmaz. Herdr'a metin gönderilmez; son metin işlem bittiğinde odaktaki alana yapıştırılır. Konuşurken veya çözümleme sürerken odağı değiştirmek yapıştırma yerini değiştirir.
Kullanım ve sınırlar [nasıl çalışır](docs/nasil-calisir.md#dikte), kaynak/çıktı akışı [mimari şemasında](docs/mimari.md) anlatılır.

### Ortam değişkenleri

`.env` (repo kökünde, `KEY=VALUE` satırları) veya sistem ortamından okunur. Hepsi isteğe bağlıdır.

| Değişken | Etkisi |
|---|---|
| `VOICEDICTATION_DATA_DIR` | Veri kökünü değiştirir; `media/`, `raw/` ve `transcripts/` bu klasörün altında oluşur. Varsayılan: `data/`. |
| `VOICEDICTATION_EDITOR` | Toplantı transkriptini açan editör (`notepad++`, `obsidian`, `subl` …). `none` ise dosya yolu yalnız panoya kopyalanır. Varsayılan sıra: VS Code → sistem varsayılanı → pano. |
| `VOICEDICTATION_QUEUE_DIR` | `file_queue.py` kuyruk kökü. Varsayılan: `.local/file-queue/`. |

## Belgeler

Belge sorumlulukları ve bakım düzeni: [docs/README.md](docs/README.md).

| Belge | Görevi |
|---|---|
| [README.md](README.md) | İnsan girişi: ne yapar, kurulum, kullanım, yerel dosyalar |
| [CLAUDE.md](CLAUDE.md) | Ajan kuralları ve değişmezler (Claude Code ve Codex okur) |
| [docs/mimari.md](docs/mimari.md) | Dikte, konuşma bağlamı, model ve çıktı akış şeması |
| [docs/nasil-calisir.md](docs/nasil-calisir.md) | Modların akışı, tray menüsü, çıktı biçimi, halüsinasyon katmanları, ayarlar |
| [docs/kurulum.md](docs/kurulum.md) | Windows/macOS kurulumu, otomatik başlatma, macOS izinleri, yeni cihaza taşıma |
| [docs/TODO.md](docs/TODO.md) | Açık işler ve Mac doğrulama listesi |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Tamamlanan işler, en yeni üstte |
| [docs/calibration/](docs/calibration/README.md) | Kalibrasyon okuma metni ve yöntemi |

## Katkı

`master` dalına yalnız repo sahibi push eder. Diğer katkıcılar `feature/<konu>` dalı açıp Pull Request gönderir.

## Teknoloji

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Windows), [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) (macOS), [sounddevice](https://python-sounddevice.readthedocs.io/), [pynput](https://pynput.readthedocs.io/), [pyperclip](https://github.com/asweigart/pyperclip), [pystray](https://pystray.readthedocs.io/) + Pillow (Windows tepsisi), [rumps](https://rumps.readthedocs.io/) (macOS menü çubuğu), numpy.

## Lisans

[MIT](LICENSE). Serbestçe kullanabilir, değiştirebilir ve dağıtabilirsin; telif notunu koru.
