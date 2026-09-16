# TODO — VoiceDictation

Bu dosyada yalnız açık işler durur. Kapanan madde buradan silinir ve [CHANGELOG.md](CHANGELOG.md) dosyasına yazılır.

## Mac'te ilk oturum

**Ajan:** Mac'te açılan ilk oturumda bu listeyi Yiğit'e öner. Son Mac doğrulaması 26 Nisan 2026'da yapıldı. O tarihten sonraki bütün değişiklikler yalnız Windows'ta doğrulandı: Mayıs'taki halüsinasyon paketleri, ad penceresi, toplantı WAV'ı ve 16 Eylül'deki yapı sadeleştirmesi.

- [ ] `git pull`, ardından `./scripts/setup.sh` çalıştır. `requirements.txt` artık `rumps` ve `mlx-whisper` paketlerini de kuruyor. macOS bağımlılık çözümü Windows'tan yalnız yaklaşık denendi; kurulumun temiz bir venv'de hatasız bittiğini doğrula. Sonra `venv/bin/python -m py_compile dictation.py`.
- [ ] İsteğe bağlı: Windows'taki `data/` klasörünü kopyala (cihazlar arası eşitleme yok).
- [ ] `scripts/VoiceDictation.app` uygulamasını `path to me` betiğiyle yeniden derle, imzala, Login Items'a yeniden ekle ve dört izni doğrula ([kurulum.md](kurulum.md)). Repodaki mevcut `.app` içinde eski, sabit bir repo yolu var.
- [ ] Daemon'ı `.app` ile başlat: menü çubuğu simgesi açılıyor mu, Caps Lock x2 ile dikte ve yapıştırma çalışıyor mu?
- [ ] `data/inbox/`, `data/audio/`, `data/transcripts/` ve `.local/logs/<YYYY-MM-Ay>.log` repo altında oluşuyor mu?
- [ ] "Ses dosyasını dök" ve "Meet Dictation" dosya seçicileri `data/inbox/` klasöründe açılıyor mu (osascript `default location`)?
- [ ] Halüsinasyon paketi 2 (B1–B4) testleri:
  - 2–3 dakikalık, uzaktan mikrofonlu ve bilerek sessizlik bırakılmış bir toplantı kaydı: son transkriptte "Altyazı M.K." benzeri tekrar olmamalı.
  - "Eee Eee Eee": tek örneğe inmeli.
  - "Evet evet evet katılıyorum": korunmalı.
- [ ] Toplantı kaydı:
  - Durdurunca osascript ad penceresi açılıyor mu?
  - WAV `data/audio/` altına yazılıyor mu?
  - `LIVE.md` temp klasöründe oluşup kayıt bitince siliniyor mu?
- [ ] `--transcribe` ile `.qta` ve `.m4a`: ses `data/audio/` klasörüne taşınıyor mu, transkript `data/transcripts/` altına yazılıyor mu, Kaynak satırı göreli mi? iCloud'dan gelen dosyada taşıma izni sorunu çıkıyor mu?
- [ ] Aynı adla ikinci kayıt zaman eki alıyor mu (üstüne yazma olmamalı)?
- [ ] Sonuçları [CHANGELOG.md](CHANGELOG.md) dosyasına yaz, bu bölümü kapat.

## Açık işler

### Ayarlar

- [ ] Ayar dosyası (JSON/YAML): kodda sabit duran ayarları (eşikler, model, cihaz, kısayol tuşu, wake word, `LECTURE_AGGRESSIVE_CLEANUP`) dışarı al.
- [ ] Wake word değişikliğini diske kaydet (şu an yeniden başlatınca varsayılana dönüyor).
- [ ] Yeni wake word'ler için Whisper yazım varyasyonu kalıplarını kendiliğinden genişlet.

### Test

- [ ] Birim testleri: durum makinesi, wake word kalıpları, `extract_message`, ses tamponu, `_dedupe_repeated_segments`, `_drop_low_confidence_segments`. `tests/` klasöründe şu an yalnız `file_queue` testleri var (`venv\Scripts\python -m unittest discover -s tests`).
- [ ] Durum makinesi geçişleri için thread güvenliği regresyon testi.

### Çıktı ve arayüz

- [ ] Hedef pencere seçimi: metni aktif pencere yerine seçilen bir pencereye yaz.
- [ ] Çoklu proje: farklı wake word'lerle farklı hedeflere yönlendirme.
- [ ] Toplantı transkripti hazır olduğunda bildirim göster (Windows toast, macOS rumps).

### Kalibrasyon

- [ ] B grubu düzeltmeleri (branch ← "bir an", refactor ← "reflektör", commit ← "komit") regex'e uymuyor; `hotwords` ile çözümleme önceliği bekliyor.

## Gelecek

- [ ] **Konuşmacı ayırmayı isteğe bağlı olarak geri aç.** Kod `dictation.py` içinde duruyor ama tray'den çağrılmıyor. Paketleri `requirements.txt` içinde yorum satırı, model `.local/models/` altında.
  - Açma seçenekleri:
    1. Yeni tray öğesi: "🎥 Meet Dictation (konuşmacı ayır)…"
    2. `--diarize` bayrağı
    3. Tek pencerede konuşmacı sayısı sorusu (0 = ayırma yok)
  - **Önce hata çözülmeli:** Meet mp4 kayıtlarında konuşmacılar yanlış kümeleniyor ve transkriptin tamamı tek konuşmacıya yapışıyor (Windows, 22 Mayıs 2026).
  - Çözüm planı:
    1. Bilinen konuşmacı sayısıyla kısa bir dosyada gömme çıktısını logla (küme sayısı, mesafe matrisi, eşik kararı).
    2. Küme sayısı mı 1'e düşüyor (düşük eşik), yoksa benzerlik mi yanlış? Hangisi olduğunu ayırt et.
    3. Eşik ve benzerlik ayarı (kosinüs + dinamik eşik).
    4. Gerekirse konuşmacı değişim sınırı tespiti.
  - Referans dosya: `data/audio/2026-05-01_Sonar-2-Dogu-teknik-toplanti.mp4` (~34 MB, 16 dakika, iki konuşmacı).
- [ ] **`file_queue` daemon bağlantısı:** Modül ve testleri hazır, ama `dictation.py` modülü içe aktarmıyor. Bağlanınca kuyruk dış istemcilerin ses dosyalarını daemon'ın açık modeliyle işler.
- [ ] **`--calibrate` akışı:** Yöntem [calibration/README.md](calibration/README.md) dosyasında anlatılıyor, akış henüz yazılmadı. Kapsamı: okuma kaydı, `jiwer` ile karşılaştırma ve önerilen düzeltme tablosu.
- [ ] **Yedek filtresi (ayrı onay):** `Yazilim` yedeğinin rclone filtresine `- /VoiceDictation/.local/` ekle. `data/` yedekte kalmalı.
- [ ] **Sonar belgeleri:** Sonar projesindeki eski Drive kayıt klasörü referanslarını yeni yerle (`VoiceDictation/data/audio/`) güncelle. Bu iş Sonar oturumunda yapılır.
- [ ] **HF önbelleği (ayrı onay):** Kullanılmayan `medium` ve `small` Whisper modelleri (~1,9 GB) silinebilir. `large-v3`, iFonzo ses aracının kullanıp kullanmadığı doğrulanmadan silinmez.
