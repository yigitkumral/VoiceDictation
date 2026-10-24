# VoiceDictation mimarisi

Ses Windows'ta yerel Whisper ile çözülür. Konuşma bağlamı Whisper'a kısa bir ipucudur; yazının gideceği
alanı seçmez. Son metin çözümleme ve temizlik bittiğinde odaktaki alana pano üzerinden yapıştırılır.
Dikte sonunda otomatik Enter yoktur; Windows boşta F13 çift hızlı basış ayrı ve açık Enter hareketidir.

```mermaid
flowchart TD
    Window[Öndeki terminal] --> Match{Tek tam başlık eşleşmesi var mı?}
    Menu[Bağlam kaynağı: açık makine ve pane seçimi] --> Verify
    Match -->|Evet| Verify[Makine + pane + terminal + agent_session doğrula]
    Match -->|Hayır ve açık seçim yok| General[Başlık / metadata / sabit terimler]
    Verify --> Local[Yerel tam ID veya yol]
    Verify --> Remote[SSH: bellekte salt okunur exporter]
    Local --> Roles[Yalnız user ve assistant / en fazla 512 KiB oku]
    Remote --> Roles
    Roles --> Check[Okuma sonrası terminal ve oturum kimliğini tekrar doğrula]
    Check --> Cache[RAM: son 300 kelime / 5 sn önbellek]
    Cache --> Budget[En fazla 160 token konuşma + 40 token terim]
    General --> Budget
    Mic[Mikrofon / RAM ses tamponu] --> Stop[F13 kaydı bitir]
    Stop --> Whisper[Tam ses: tek Whisper çözümlemesi]
    Budget -->|En fazla 150 ms bekleme| Whisper
    Whisper --> Cleanup[Hazırsa yerel Qwen / CUDA veya CPU]
    Cleanup --> Filter{Sayı, ad, literal ve anlam koruması}
    Filter -->|Kabul| Final[Son metin]
    Filter -->|Ret / hata / hazır değil| Raw[Ham Whisper metni]
    Raw --> Final
    Final --> Clipboard[Pano]
    Clipboard --> Focus[İşlem sonunda odaktaki alana tek yapıştırma]
    Whisper --> Metrics[İçeriksiz süre / uzunluk / durum ölçümü]
    Cleanup --> Metrics
    Focus --> Metrics
    Metrics --> Tray[Tray bağlam ve süre özeti]
```

Kaynak kontrolü arka planda yaklaşık 0,75 saniyede bir çalışır, Herdr envanteri yaklaşık 15 saniyede
yenilenir. Genel başlıktan “en yeni” veya sunucuda o an odaktaki oturum tahmin edilmez. Tek bir tam
başlık eşleşmesi yoksa **Bağlam kaynağı** menüsünden seçim gerekir. Manuel seçim uygun terminal
penceresinin hwnd/PID kimliğine bağlanır; Chrome veya başka pencerede kaynak kullanılmaz. Aynı pencere
içindeki sekme değişimi algılanmadığından açık seçim güncellenmelidir.

`agent_session`, sağlayıcı (`codex`/`claude`), tür (`id`/`path`), değer ve kaynak alanlarıyla doğrulanmış
oturum kaydını belirtir. Herdr'ın mevcut oturum başlangıç hook'ları bu alanı verebilir; eski oturumlar
kayıtsız olabilir. Terminal süreç argv'si tek başına sohbet kimliği sayılmaz. `context_bridge.py`
yalnız tam ID/yol çözümlemesi yapar; alt ajan, sistem ve araç metinlerini dışlar. `context_source.py`
yerel/SSH okumayı kimlik kontrolü ve RAM önbelleğiyle yönetir. Uzak exporter stdin üzerinden çalışır;
uzak makineye dosya yazmaz veya paket kurmaz. Herdr terminal çıktısı, ilgisiz oturum veya rastgele son
değişen kayıt okunmaz.

Whisper'ın ipucuna 300 kelimenin tamamı girmez. Gerçek HF tokenizer ile konuşmanın son kısmı 160,
terimler 40 token ile kesilir; toplam en fazla 200 token, 223 sınırının altındadır. Tokenizer olmayan
Mac yolunda daha muhafazakâr UTF-8 byte sınırı kullanılır. Bağlam için ayrı bir dil modeli çalışmaz.
Kaynak hazır değilse veya kimlik değişmişse genel ipuçlarıyla dikte devam eder.

Qwen ayrı kalıcı yerel alt süreçtir. Mevcut model CUDA0 doğrulanırsa GPU'ya yüklenir; başlatma,
ön ısıtma veya çalışma zamanı GPU hatasında CPU yedeği vardır. Hazır olmayan model bekletmez; ham
metin korunur. Temizlik en fazla 1200 karakter ve 12 saniye ile sınırlıdır. Normal kapanış yalnız
uygulamanın sahip olduğu süreci kapatır.

Konuşma bağlamı için yeni transkript veya günlük kopyası oluşturulmaz. `.local/metrics/dictation.jsonl`
yalnız süre/uzunluk/durum ve izin verilen backend değerini tutar; konuşma, pencere/pane adı içermez.
Mevcut aylık dikte log politikası ayrıdır. Yerel dosyaların tam listesi
[README tablosunda](../README.md#yerel-dosyalar), kullanıcı akışı [nasıl çalışır](nasil-calisir.md) belgesindedir.
