# TODO — VoiceDictation

Bu dosyada yalnız açık işler durur. Kapanan madde buradan silinir ve [CHANGELOG.md](CHANGELOG.md) dosyasına yazılır.

- [ ] Mac'te gerçek üç parmak → kayıt → otomatik yapıştırma akışının kullanıcı kabulünü tamamla. Yeni başlatıcının mikrofon, Erişilebilirlik ve Giriş İzleme izinleri verildi; yeniden açılışta güven uyarısı yok. Eski ortam `.local/migration-20261025/` altında kullanım kabulüne kadar korunuyor.

## Mac'te ilk oturum

25 Ekim 2026: yeni yerleşimde Python 3.14.4, bağımlılıklar, 187 otomatik test ve 12 trackpad senaryosu Mac'te geçti. Yeni uygulamanın mikrofon izni verildi. Aşağıdaki gerçek kullanım kabul listesi otomatik kontrollerden ayrıdır.

**Ajan:** Mac'te çalışmaya başlamadan önce [klasör geçişi](kurulum.md#eski-klasör-düzeninden-geçiş) bölümünü izle; eski ortamı yeni yerleşim doğrulanana kadar koru.

- [ ] `git pull`, ardından `./dev/scripts/setup.sh` çalıştır. `dev/requirements.txt` artık `rumps` ve `mlx-whisper` paketlerini de kuruyor. macOS bağımlılık çözümü Windows'tan yalnız yaklaşık denendi; kurulumun temiz bir venv'de hatasız bittiğini doğrula. Sonra `.local/venv/bin/python -m py_compile dev/dictation.py`.
- [ ] İsteğe bağlı: Windows'taki `.local/data/` klasörünü kopyala (cihazlar arası eşitleme yok).
- [ ] `.local/VoiceDictation.app` uygulamasını `dev/scripts/build-mac-app.sh` ile üret; Login Items ve macOS izinlerini doğrula ([kurulum.md](kurulum.md)). Derlenmiş uygulama artık Git dışındadır.
- [ ] Daemon'ı `.app` ile başlat: menü çubuğu simgesi açılıyor mu, Caps Lock x2 ile dikte ve yapıştırma çalışıyor mu?
- [ ] `.local/data/media/`, `.local/data/raw/`, `.local/data/transcripts/` ve `.local/logs/<YYYY-MM-Ay>.log` repo altında oluşuyor mu?
- [ ] "Ses dosyasını dök" ve "Meet Dictation" dosya seçicileri `.local/data/media/` klasöründe açılıyor mu (osascript `default location`)?
- [ ] Halüsinasyon paketi 2 (B1–B4) testleri:
  - 2–3 dakikalık, uzaktan mikrofonlu ve bilerek sessizlik bırakılmış bir toplantı kaydı: son transkriptte "Altyazı M.K." benzeri tekrar olmamalı.
  - "Eee Eee Eee": tek örneğe inmeli.
  - "Evet evet evet katılıyorum": korunmalı.
- [ ] Toplantı kaydı:
  - Durdurunca osascript ad penceresi açılıyor mu?
  - WAV `.local/data/media/` altına yazılıyor mu?
  - `LIVE.md` temp klasöründe oluşup kayıt bitince siliniyor mu?
- [ ] `--transcribe` ile `.qta` ve `.m4a`: `.local/data/media/` dışından verilen dosya oraya taşınıyor mu (içindeyse yerinde kalıyor mu), transkript `.local/data/raw/` altına yazılıyor mu, Kaynak satırı göreli mi? iCloud'dan gelen dosyada taşıma izni sorunu çıkıyor mu?
- [ ] Aynı adla ikinci kayıt zaman eki alıyor mu (üstüne yazma olmamalı)?
- [ ] Sonuçları [CHANGELOG.md](CHANGELOG.md) dosyasına yaz, bu bölümü kapat.

## Dikte iyileştirmesi — gerçek kullanım kabulü

- [ ] Mac trackpad kalan kabul: aynı sürece alınan, basmayı da kabul eden sürümde ses + kayıt/bitiş/yapıştırma; kaydırma/iki-dört parmak reddi, mevcut sistem hareketleriyle çakışma, çift hareketle Enter ve uyku dönüşü. İlk ayrı TP prototipinin kayıt/bitiş/yapıştırması Yiğit ile doğrulanmıştı. Özel MultitouchSupport API'si her macOS güncellemesinde tekrar sınanmalı.

- [ ] Vault cihaz tanısı: gerçek iPhone/iPad/masaüstü tarayıcı kayıtlarında cihaz türü, aynı profilde sabit istemci kimliği ve her kayıtta yeni istek kimliğini doğrula; Vault teslim sonucu ile backend tanısını aynı istek kimliğiyle karşılaştır. Sentetik HTTP doğrulaması geçti; fiziksel cihaz kabulü ayrı yapılacak.

- [ ] Sade dikteyi gerçek mikrofonla doğrula: F13 başlangıç/bitiş, tek Whisper, tek yapıştırma, reset ve wake word; dikte bitişi otomatik Enter göndermemeli. Windows'ta ilk basışta hemen kayıt, bırakıştan 250 ms sonra başlangıç tonu; hızlı çift basışta kısa kaydın sessiz iptali ve tek Enter denenmeli. Kesinleşmiş kaydı durdurma anlık, işleme sırasında Enter yok. Mac değişmez. Çözümleme sırasında odak değiştirilirse metin son odaktaki alana gitmeli. [Önceki kabul kaydı](sessions/2026-10-24-gpu-double-tap/README.md).
- [ ] CUDA Qwen ile gerçek mikrofon kalitesi/gecikmesi, Whisper ile GPU paylaşımı ve VRAM tüketimini doğrula; sentetik GPU kurulumu/ölçümleri tamamlandı, gerçek kullanım kabulü açık.
- [ ] Varsayılan terminal/editör başlığı ipuçlarını ve Windows'taki isteğe bağlı **Bağlam kaynağı** menüsünü doğrula. Herdr metadata ve doğrulanmış sohbet bağlamı kaynağı olmalı; seçilen pane'e yazılmamalı. Yerel cwd/Git dalı ve varsa uzak `git_branch` metadata'sı, erişim hatası/zaman aşımında sabit listeye dönüş denenmeli.
- [ ] Yerel temizlikte gerçek Türkçe dikte kabulü: noktalama, paragraf, dolgu ve açık gün özdüzeltmesi; sayı, özel ad, teknik literal, olumsuzluk ve anlamlı tekrar koruması. 1200 karakter sınırı ve 12 saniye zaman aşımında ham metne dönüşü doğrula; gecikmeyi ölç.
- [ ] Kalıcı Qwen ile gerçek mikrofon gecikmesini ve günlük kullanım RAM tüketimini ölç. Sentetik sıcak/ilk açılış ölçümleri, hazır olmama/hata/zaman aşımı kontrolleri ve sahip olunan süreç/işçi kapanış doğrulaması tamamlandı; sonuçlar [kalıcı model kaydında](sessions/2026-10-24-warm-cleanup/README.md).
- [ ] Herdr bağlam kaynağının seçilen uygun terminal penceresinin hwnd/PID kimliğine bağlandığını doğrula: başka pencere/Chrome'da kullanılmamalı, aynı pencereye dönüşte kullanılmalı. Aynı pencere içi sekme değişimi algılanmaz; kaynak yeniden seçilmeli. Süre telemetrisinde yalnız süre/uzunluk/durum olmalı; tray özeti F13 bitişinden yapıştırmaya toplam süreyle tutarlı olmalı.
- [ ] Mac'te sade dikte, Caps Lock/reset, o an odaktaki uygulamaya yapıştırma ve isteğe bağlı yerel çalıştırıcı kabulünü tamamla. Windows başlık/Herdr bağlam kaynağı menüsünün Mac karşılığı henüz yok.

- [ ] Vault'tan uzak dikteyi gerçek cihazda doğrula: iPhone ve iPad'de `https://<makine>/` kart terminalinde mikrofon izni, kırmızı yanınca konuşma, metnin Enter'sız gelmesi, Mac pane'inde sohbet bağlamı ve gecikme. Sentetik uçtan uca ölçüm 0,6 sn (6 sn konuşma).
- [ ] Konuşma bağlamını gerçek kullanımda doğrula: doğru kaynak/oturum, user/assistant filtresi, genel başlıkta açık seçim, oturum değişimi, SSH kesilmesi ve 5 saniyelik RAM önbelleği. Yeni konuşma kopyası/logu oluşmamalı; 160+40 token sınırı ve son odaktaki alana yapıştırma korunmalı. Otomatik kontroller [konuşma bağlamı kaydında](sessions/2026-10-24-conversation-context/README.md).

## Açık işler

- [ ] [24 Ekim denetiminden kalanları](sessions/2026-10-24-denetim/uygulama.md#kapsam-dışında-kalan-denetim-bulguları) Yiğit'le değerlendir: PID kilidi, editör shell çağrısı, log politikası, toplantı thread yaşam döngüsü, kuyruk/diarize ve dosya çözümleme koşullaması.

- [ ] Ayar dosyası (JSON/YAML): kodda sabit duran ayarları (eşikler, model, cihaz, kısayol tuşu, wake word, `LECTURE_AGGRESSIVE_CLEANUP`) dışarı al.
- [ ] Wake word değişikliğini diske kaydet (şu an yeniden başlatınca varsayılana dönüyor).
- [ ] Yeni wake word'ler için Whisper yazım varyasyonu kalıplarını kendiliğinden genişlet.

- [ ] Test kapsamını genişlet: wake word kalıpları, `extract_message`, `_drop_low_confidence_segments` ve gerçek callback sıralaması. Kuyruk, iptal/yapıştırma, bağlam ve yerel temizlik regresyonları mevcut (`.local\venv\Scripts\python -m unittest discover -s dev/tests`).
- [ ] Durum makinesi geçişleri için thread güvenliği regresyon testi.

- [ ] Hedef pencere seçimi: son metni o an odaktaki alan yerine seçilen bir pencereye yazma gelecekte ayrı özellik olarak değerlendirilebilir; mevcut davranış son odaktaki alana yapıştırmadır.
- [ ] Çoklu proje: farklı wake word'lerle farklı hedeflere yönlendirme.
- [ ] Toplantı transkripti hazır olduğunda bildirim göster (Windows toast, macOS rumps).

- [ ] B grubu düzeltmeleri (branch ← "bir an", refactor ← "reflektör", commit ← "komit") için kalite ölçümü: dinamik `hotwords` eklendi, aynı kısa kayıt üzerinde etkisi doğrulanmalı.

## Gelecek

- [ ] Konuşmacı ayırmayı isteğe bağlı geri aç: tray öğesi, `--diarize` veya konuşmacı sayısı penceresi seçeneklerinden biri seçilecek. Önce Meet kayıtlarında bütün metnin tek konuşmacıya atanması çözülmeli (22 Mayıs 2026). Bilinen konuşmacı sayısıyla kısa örnekte gömme/küme sayısı, mesafe matrisi ve eşik kararı incelenecek; kosinüs/dinamik eşik, gerekirse konuşmacı değişim sınırı denenecek. Referans: `.local/data/media/2026-05-01_Sonar-2-Dogu-teknik-toplanti.mp4` (~34 MB, 16 dakika, iki konuşmacı). Kod uyuyor, paketler requirements içinde yorum satırı, model `.local/models/` altında.
- [ ] **iPhone'da her uygulamada dikte (Yiğit fikri, 24 Ekim 2026):** Bir iOS Kestirmesi sesi kaydeder, tailnet üzerinden Windows'taki uzak dikte ucuna gönderir, dönen metni panoya koyar; Yiğit istediği uygulamaya yapıştırır. HTTPS gerekmez. Uç, Vault'tan dikte için kurulan aynı Windows sunucusudur; Kestirme için ayrı kimlik/erişim kararı gerekir.
- [ ] **`file_queue` daemon bağlantısı:** Modül ve testleri hazır, ama `dev/dictation.py` modülü içe aktarmıyor. Bağlanınca kuyruk dış istemcilerin ses dosyalarını daemon'ın açık modeliyle işler.
- [ ] **`--calibrate` akışı:** Yöntem [calibration/README.md](calibration/README.md) dosyasında anlatılıyor, akış henüz yazılmadı. Kapsamı: okuma kaydı, `jiwer` ile karşılaştırma ve önerilen düzeltme tablosu.
- [ ] **Yedek filtresi (ayrı onay):** `Yazilim` yedeğinin rclone filtresine `- /VoiceDictation/.local/` ekle. `.local/data/` yedekte kalmalı.
- [ ] **Sonar belgeleri:** Sonar projesindeki eski Drive kayıt klasörü referanslarını yeni yerle (`VoiceDictation/data/media/`) güncelle. Bu iş Sonar oturumunda yapılır.
- [ ] **HF önbelleği (ayrı onay):** Kullanılmayan `medium` ve `small` Whisper modelleri (~1,9 GB) silinebilir. `large-v3`, iFonzo ses aracının kullanıp kullanmadığı doğrulanmadan silinmez.
