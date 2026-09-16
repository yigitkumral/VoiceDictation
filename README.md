# VoiceDictation

Yerel Whisper modeliyle çalışan, Windows ve macOS'ta kullanılan sesli yazım aracı. Konuşmanı metne çevirir, aktif pencereye yapıştırır ve Enter gönderir. Toplantı ve ders kayıtlarını canlı izlenebilen Markdown transkriptlerine, mevcut ses ve video dosyalarını da yüksek kaliteli transkriptlere dönüştürür. İnternet gerekmez; ses makineden çıkmaz.

> **Türkçe için özelleştirildi.** Whisper `language="tr"` ile çalışır. Kelime listesi (`INITIAL_PROMPT`), halüsinasyon filtreleri ve "Diktasyon" wake word varyasyonları Türkçe çıktılara göre yazıldı. Arayüz, log ve yorumlar Türkçedir; başka dil için kod uyarlaması gerekir.

## Özellikler

- **Anlık dikte:** F13 (Windows) veya Caps Lock x2 (macOS) ile kayıt aç/kapat; metin aktif pencereye yapıştırılıp gönderilir.
- **Wake word:** "Diktasyon" diyerek başlat ve bitir (varsayılan kapalı, tray'den açılır).
- **Toplantı modu:** Uzun kayıtta canlı transkript editörde akar; kayıt bitince sesi WAV olarak saklar ve yüksek kaliteli son transkripti yazar.
- **Dosyadan transkript:** AAC, MP3, WAV, M4A, iPhone `.qta` ve MP4 gibi video dosyaları dahil; tray'den veya `--transcribe` ile.
- **GPU:** Windows'ta CUDA (yoksa CPU'ya düşer), macOS'ta Apple Silicon üzerinde MLX.

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
| Kaydı başlat / bitir ve gönder | F13 | Caps Lock iki kez |
| Sesle başlat / bitir | "Diktasyon" | "Diktasyon" |
| Kaydı iptal et | F13'ü 1,25 sn basılı tut | Caps Lock üç kez |
| Toplantı kaydı, dosya dökme, Meet Dictation | Tray → 🎤 Toplantı | Menü çubuğu → 🎤 Toplantı |

Dosya seçiciler `data/inbox/` klasöründe açılır: işlenecek ses veya video dosyasını önce oraya bırak. Daemon kapalıyken komut satırından da çevirebilirsin:

```bash
venv\Scripts\python dictation.py --transcribe "data\inbox\kayit.m4a"     # Windows
venv/bin/python dictation.py --transcribe "data/inbox/kayit.qta"         # macOS
```

Modların adım adım akışı, tray menüsü, çıktı biçimi ve ayarlar: [docs/nasil-calisir.md](docs/nasil-calisir.md).

## Yerel dosyalar

Git yalnız kodu ve belgeleri taşır. Aşağıdaki tablo projenin makinede tuttuğu her şeyin **tek** listesidir; yol veya klasör değişirse önce burası güncellenir.

| Yol | İçerik | Sınıf | Yeni cihazda |
|---|---|---|---|
| `data/inbox/` | Elle bırakılan ses/video dosyaları (Meet kayıtları, iPhone kayıtları). Program buradaki dosyayı yalnız "dök" akışında `data/audio/`'ya taşır; başka hiçbir şey yapmaz. | Değerli, git dışı | Kopyalanır |
| `data/audio/` | Toplantı kayıtlarının WAV'ları ve işlenmiş ses dosyaları | Değerli, git dışı | Kopyalanır |
| `data/transcripts/` | Markdown transkriptler | Değerli, git dışı | Kopyalanır |
| `.local/logs/` | Aylık log (`YYYY-MM-<Ay>.log`, örn. `2026-09-Eylul.log`; dikte metni dahil tam içerik, silinmez) ve `dictation.pid` | Makineye özel, git dışı | Kendiliğinden oluşur |
| `.local/models/` | speechbrain modeli (uyuyan konuşmacı ayırma özelliği) | Makineye özel, git dışı | Gerekirse kendiliğinden iner |
| `.local/file-queue/` | `file_queue.py` iş kuyruğu (daemon'a bağlı değil) | Makineye özel, git dışı | Kendiliğinden oluşur |
| `venv/` | Python ortamı | Platforma özel, git dışı | `scripts/setup.*` ile kurulur |
| `.env` | İsteğe bağlı ortam değişkenleri (aşağıda); bugün kullanılmıyor | Makineye özel, git dışı | Gerekirse elle oluşturulur |
| `~/.cache/huggingface/hub/` | Whisper turbo modeli (Windows: `mobiuslabsgmbh/faster-whisper-large-v3-turbo`, macOS: `mlx-community/whisper-turbo`). Önbellek başka projelerle ortaktır; buradaki diğer modeller silinmez. | Repo dışı | İlk açılışta iner |
| Sistem temp → `voicedictation_live/` | Toplantı sırasında canlı `LIVE.md` ve geçici WAV | Repo dışı, geçici | Kendiliğinden oluşur, kayıt bitince silinir |
| Windows Startup → `VoiceDictation.lnk` | `scripts\start.vbs` kısayolu | Repo dışı | `scripts\setup.bat` oluşturur |
| macOS Login Items → `VoiceDictation` | `scripts/VoiceDictation.app` | Repo dışı | Elle eklenir ([kurulum](docs/kurulum.md)) |

**Yeni cihaza taşıma özeti:** Yalnız `data/` kopyalanır. Geri kalan her şey kurulumla ya da ilk çalıştırmada yeniden oluşur. Cihazlar arasında veri eşitlemesi yoktur.

`data/` ile `.local/` klasörleri program ilk açıldığında oluşur. Programı kullanmak git durumunu değiştirmez.

### Ortam değişkenleri

`.env` (repo kökünde, `KEY=VALUE` satırları) veya sistem ortamından okunur. Hepsi isteğe bağlıdır.

| Değişken | Etkisi |
|---|---|
| `VOICEDICTATION_DATA_DIR` | Veri kökünü değiştirir; `inbox/`, `audio/` ve `transcripts/` bu klasörün altında oluşur. Varsayılan: `data/`. |
| `VOICEDICTATION_EDITOR` | Toplantı transkriptini açan editör (`notepad++`, `obsidian`, `subl` …). `none` ise dosya yolu yalnız panoya kopyalanır. Varsayılan sıra: VS Code → sistem varsayılanı → pano. |
| `VOICEDICTATION_QUEUE_DIR` | `file_queue.py` kuyruk kökü. Varsayılan: `.local/file-queue/`. |

## Belgeler

| Belge | Görevi |
|---|---|
| [README.md](README.md) | İnsan girişi: ne yapar, kurulum, kullanım, yerel dosyalar |
| [CLAUDE.md](CLAUDE.md) | Ajan kuralları ve değişmezler (Claude Code ve Codex okur) |
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
