# TODO — VoiceDictation

Bu dosyada yalnız açık işler durur. Kapanan madde buradan silinir ve [CHANGELOG.md](CHANGELOG.md) dosyasına yazılır.

## Mac'te ilk oturum

**Ajan:** Mac'te açılan ilk oturumda bu listeyi Yiğit'e öner. Son Mac doğrulaması 26 Nisan 2026'da yapıldı. O tarihten sonraki bütün değişiklikler yalnız Windows'ta doğrulandı: Mayıs'taki halüsinasyon paketleri, ad penceresi, toplantı WAV'ı ve 16 Eylül'deki yapı sadeleştirmesi.

- [ ] `git pull`, ardından `./scripts/setup.sh` çalıştır. `requirements.txt` artık `rumps` ve `mlx-whisper` paketlerini de kuruyor. macOS bağımlılık çözümü Windows'tan yalnız yaklaşık denendi; kurulumun temiz bir venv'de hatasız bittiğini doğrula. Sonra `venv/bin/python -m py_compile dictation.py`.
- [ ] İsteğe bağlı: Windows'taki `data/` klasörünü kopyala (cihazlar arası eşitleme yok).
- [ ] `scripts/VoiceDictation.app` uygulamasını `path to me` betiğiyle yeniden derle, imzala, Login Items'a yeniden ekle ve dört izni doğrula ([kurulum.md](kurulum.md)). Repodaki mevcut `.app` içinde eski, sabit bir repo yolu var.
- [ ] Daemon'ı `.app` ile başlat: menü çubuğu simgesi açılıyor mu, Caps Lock x2 ile dikte ve yapıştırma çalışıyor mu?
- [ ] `data/media/`, `data/raw/`, `data/transcripts/` ve `.local/logs/<YYYY-MM-Ay>.log` repo altında oluşuyor mu?
- [ ] "Ses dosyasını dök" ve "Meet Dictation" dosya seçicileri `data/media/` klasöründe açılıyor mu (osascript `default location`)?
- [ ] Halüsinasyon paketi 2 (B1–B4) testleri:
  - 2–3 dakikalık, uzaktan mikrofonlu ve bilerek sessizlik bırakılmış bir toplantı kaydı: son transkriptte "Altyazı M.K." benzeri tekrar olmamalı.
  - "Eee Eee Eee": tek örneğe inmeli.
  - "Evet evet evet katılıyorum": korunmalı.
- [ ] Toplantı kaydı:
  - Durdurunca osascript ad penceresi açılıyor mu?
  - WAV `data/media/` altına yazılıyor mu?
  - `LIVE.md` temp klasöründe oluşup kayıt bitince siliniyor mu?
- [ ] `--transcribe` ile `.qta` ve `.m4a`: `data/media/` dışından verilen dosya oraya taşınıyor mu (içindeyse yerinde kalıyor mu), transkript `data/raw/` altına yazılıyor mu, Kaynak satırı göreli mi? iCloud'dan gelen dosyada taşıma izni sorunu çıkıyor mu?
- [ ] Aynı adla ikinci kayıt zaman eki alıyor mu (üstüne yazma olmamalı)?
- [ ] Sonuçları [CHANGELOG.md](CHANGELOG.md) dosyasına yaz, bu bölümü kapat.

## Dikte iyileştirmesi — gerçek kullanım kabulü

- [ ] Sonraki daemon başlatmasında kısa onaylı kayıtla önizleme, F13/reset, odak değişimi ve tek gönderimi doğrula; aynı kayıtla önce/sonra kalite ve gecikme kıyası yap. Otomatik/sentetik kontroller [uygulama kaydında](sessions/2026-10-24-denetim/uygulama.md).
- [ ] Etkin Herdr pane/proje değişimini gerçek masaüstünde doğrula; çok istemcili Herdr sunucusunda odak farklılığına bak.
- [ ] Mac'te yeni menü önizlemesi, Herdr bağlamı, uygulama hedefi kontrolü ve isteğe bağlı yerel çalıştırıcıyı doğrula. Windows VS Code başlık bağlamının Mac karşılığı henüz yok.
- [ ] Yerel temizlikte gerçek Türkçe dikte kabulü: dolgu ve açık gün düzeltmeleri dışındaki kendi kendini düzeltmeler bugün muhafazakâr filtreyle özgün metne döner. Genişletme için anlam koruma ölçümü gerekir.

## Açık işler

- [ ] [24 Ekim denetiminden kalanları](sessions/2026-10-24-denetim/uygulama.md#kapsam-dışında-kalan-denetim-bulguları) Yiğit'le değerlendir: PID kilidi, editör shell çağrısı, log politikası, toplantı thread yaşam döngüsü, kuyruk/diarize ve dosya çözümleme koşullaması.

- [ ] Ayar dosyası (JSON/YAML): kodda sabit duran ayarları (eşikler, model, cihaz, kısayol tuşu, wake word, `LECTURE_AGGRESSIVE_CLEANUP`) dışarı al.
- [ ] Wake word değişikliğini diske kaydet (şu an yeniden başlatınca varsayılana dönüyor).
- [ ] Yeni wake word'ler için Whisper yazım varyasyonu kalıplarını kendiliğinden genişlet.

- [ ] Test kapsamını genişlet: wake word kalıpları, `extract_message`, `_drop_low_confidence_segments` ve gerçek callback sıralaması. Kuyruk, iptal/gönderim, bağlam, önizleme ve yerel temizlik regresyonları mevcut (`venv\Scripts\python -m unittest discover -s tests`).
- [ ] Durum makinesi geçişleri için thread güvenliği regresyon testi.

- [ ] Hedef pencere seçimi: metni aktif pencere yerine seçilen bir pencereye yaz.
- [ ] Çoklu proje: farklı wake word'lerle farklı hedeflere yönlendirme.
- [ ] Toplantı transkripti hazır olduğunda bildirim göster (Windows toast, macOS rumps).

- [ ] B grubu düzeltmeleri (branch ← "bir an", refactor ← "reflektör", commit ← "komit") için kalite ölçümü: dinamik `hotwords` eklendi, aynı kısa kayıt üzerinde etkisi doğrulanmalı.

## Gelecek

- [ ] Konuşmacı ayırmayı isteğe bağlı geri aç: tray öğesi, `--diarize` veya konuşmacı sayısı penceresi seçeneklerinden biri seçilecek. Önce Meet kayıtlarında bütün metnin tek konuşmacıya atanması çözülmeli (22 Mayıs 2026). Bilinen konuşmacı sayısıyla kısa örnekte gömme/küme sayısı, mesafe matrisi ve eşik kararı incelenecek; kosinüs/dinamik eşik, gerekirse konuşmacı değişim sınırı denenecek. Referans: `data/media/2026-05-01_Sonar-2-Dogu-teknik-toplanti.mp4` (~34 MB, 16 dakika, iki konuşmacı). Kod uyuyor, paketler requirements içinde yorum satırı, model `.local/models/` altında.
- [ ] **`file_queue` daemon bağlantısı:** Modül ve testleri hazır, ama `dictation.py` modülü içe aktarmıyor. Bağlanınca kuyruk dış istemcilerin ses dosyalarını daemon'ın açık modeliyle işler.
- [ ] **`--calibrate` akışı:** Yöntem [calibration/README.md](calibration/README.md) dosyasında anlatılıyor, akış henüz yazılmadı. Kapsamı: okuma kaydı, `jiwer` ile karşılaştırma ve önerilen düzeltme tablosu.
- [ ] **Yedek filtresi (ayrı onay):** `Yazilim` yedeğinin rclone filtresine `- /VoiceDictation/.local/` ekle. `data/` yedekte kalmalı.
- [ ] **Sonar belgeleri:** Sonar projesindeki eski Drive kayıt klasörü referanslarını yeni yerle (`VoiceDictation/data/media/`) güncelle. Bu iş Sonar oturumunda yapılır.
- [ ] **HF önbelleği (ayrı onay):** Kullanılmayan `medium` ve `small` Whisper modelleri (~1,9 GB) silinebilir. `large-v3`, iFonzo ses aracının kullanıp kullanmadığı doğrulanmadan silinmez.
