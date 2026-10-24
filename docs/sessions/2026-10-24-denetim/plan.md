# Dikte iyileştirmesi — onaylanan uygulama planı

Yiğit bu planı ve önerilen düzeltmeleri onayladı. Model indirmesi de sonraki ayrı soruda onaylandı.
Seçilen düzeltmeler: iptal/gönderim, dosya çakışması, hata toparlama ve tekrar temizliği.
Uygulama sonucu ve platform sınırları [uygulama kaydındadır](uygulama.md).

## 1. Dinamik bağlam

Kayıt başında yalnız etkin pencere/pane için ad ve çalışma klasörü metadata'sı alınır; başka oturum
listeleri, transkriptler ve ekran içeriği taranmaz. Güvenilir klasör bulunduğunda yalnız o repoda
`git symbolic-ref --short HEAD` benzeri salt okunur, kısa zaman aşımlı çağrı kullanılır. Pencere başlığı
tek başına dal/klasör tahmini için yeterli sayılmaz. Herdr'da odaktaki pane bilgisinin desteklenen
API ile doğru eşlenmesi uygulama sırasında doğrulanır; daemon'ın miras ortam değişkenine güvenilmez.
Bağlam alınamazsa sabit ipucuyla devam edilir.

Proje, dal ve dosya adları sınırlı sayıda/uzunlukta terime çevrilir; kontrol karakterleri, URL ve
adres benzeri değerler dışlanır. Başlıkta görünen cümleler talimat sayılmaz. Dosya içeriği okunmaz.
faster-whisper için `hotwords`, MLX için sınırlı `initial_prompt` kullanılır; kurulu faster-whisper
kaynağı iki seçeneği de destekliyor. Wake word algılama yoluna dinamik terim eklenmez. Bağlam yeni
kayıtla yenilenir ve loga ham başlık yazılmaz. Dosya transkripti masaüstünün bağlamını otomatik almaz.

Kabul: iki proje arasında geçiş, Git dışı pencere, detached HEAD, zaman aşımı, boş/çok uzun/kötü
biçimli başlık ve eski Herdr ortamı test edilir. Bağlam bulunamaması dikteyi engellemez.

## 2. Geçici metin ve tam sesle son tur

Tek Whisper modeli korunur. Kayıt sırasında sınırlı ses penceresi, yaklaşık 2–3 saniye aralıkla ve
birikmiş iş kuyruğu oluşturmadan çözülür. Geçici metin odağı almayan küçük bir önizlemede gösterilir;
panoya veya hedef uygulamaya yazılmaz. Son tur tam kayıt tamponunu kullanır, geçici metni girdi almaz.
Final iş önceliklidir; devam eden model çağrısı bitince yeni geçici çağrı başlamaz. Son metin bir kez
gönderilir. İptal/yeni kayıt kimliği eski sonuçların hem önizlemeye hem gönderime ulaşmasını engeller.

Stop-word checker ile aynı sesi iki kez çözen bağımsız döngüler kurulmaz. Ortak geçici sonuç stop
algılamada kullanılabilir; mevcut wake başlat/durdur davranışı korunur. Başlangıç hedefi Windows;
Mac için önizleme UI'si ayrı platform adaptasyonu ve gerçek cihaz kabulü gerektirir. F13/Caps Lock,
CLI ve toplantı transkript biçimi korunur. Önizleme aç/kapat seçeneği Ayarlar menüsüne eklenir.

Kabul: konuşurken değişen önizleme, hızlı durdurma, reset, yeni kayıt, model hatası, toplantı modu,
tek gönderim ve gerçek sesle gecikme/RAM ölçümü. Sahte model testleri önce, daemon yeniden başlatma
ve canlı mikrofon denemesi Yiğit'in bilgisiyle sonra yapılır.

## 3. İsteğe bağlı yerel temizlik

Varsayılan kapalı bir Ayarlar seçeneği. Yalnız son dikte metni, kurulu küçük yerel modele gider;
bulut, Anthropic iç uç noktası veya otomatik model indirme kullanılmaz. Çıktı biçimi yalnız metindir;
metindeki emirler çalıştırılmaz. Sayı, tarih, özel ad ve olumsuzluk değişimi denetlenir; boş/uzun,
şüpheli sonuçta veya zaman aşımında Whisper metni korunur. Bu kontroller anlam koruma garantisi
vermez; Türkçe düzeltme örnekleriyle kabul gerekir.

Model ve çalıştırıcı seçimi mevcut kurulum/VRAM kapasitesi metadata'sına göre yapılır. Yeni dosya
gerekiyorsa önce tam model, lisans, indirme boyutu ve kaynak sunulur; ayrı onay olmadan indirilmez.
Model yokken temizlik kapalı kalır; yalnız bağlantı kodunun yazılması tamamlanmış kalite doğrulaması
sayılmaz. Genel amaçlı ayar sistemi veya ayrı servis altyapısı bu işin kapsamına eklenmez.

Kabul: dolgu temizliği, “salı, hayır çarşamba” düzeltmesi, sayı/tarih/olumsuzluk koruması, anlamlı
tekrarların korunması, model yokluğu ve zaman aşımı. Yeni çalışma dosyaları `.local/` altında;
`data/transcripts/` program çıktısı için kullanılmaz.

## Teslim

Her adım ayrı doğrulanır, kullanım belgeleri ve TODO/CHANGELOG güncellenir. Dikte kalitesi öncesi/sonrası
aynı onaylı kısa kayıtla karşılaştırılır; özel geçmiş sesler kendiliğinden okunmaz. Commit için ayrıca
“Commit yapayım mı?” sorulur. Commit/push onayı uygulama veya indirme onayından türetilmez.
