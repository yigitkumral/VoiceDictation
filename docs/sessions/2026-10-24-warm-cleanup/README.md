# 24 Ekim 2026 — Kalıcı Qwen, pencereye bağlı bağlam ve süre ölçümü

## Onaylanan değişiklik

Tek sefer dikte korunur: F13 bitişi → tek Whisper → açıksa yerel temizlik → o anda odaktaki alana tek
pano yapıştırması. Otomatik Enter, canlı önizleme/terminal taslağı ve Herdr'a teslimat yoktur.
Bu tur yerel temizlik modelini bellekte tutarak tekrar yükleme maliyetini azaltmayı ve bekleme
aşamalarını metin içeriği tutmadan ölçmeyi amaçlar. Önceki [sade dikte kaydı](../2026-10-24-sade-dikte/README.md)
tarihçe olarak korunur.

## Kalıcı model

- Mevcut Qwen modeli başlangıçta arka plandaki `llama-server` alt sürecine yüklenir; yeni indirme yoktur.
- Model/çalıştırıcı mevcutsa temizlik başlangıçta açıktır; tray'den kapatılabilir. Model henüz hazır
  değilse dikte yüklenmesini beklemeden ham Whisper metniyle devam eder.
- Menü **(hazır)** / **(hazır değil)** / **(model yok)** durumunu gösterir. Kapalı temizliği açmak
  başlangıç veya yeniden denemeyi tetikler.
- Sunucu yalnız loopback adresinde geçici port ve rastgele erişim anahtarı kullanır; dış ağa açılmaz,
  sistem servisi kurulmaz. Normal kapanışta yalnız uygulamanın sahip olduğu alt süreç kapatılır.
- İstek için 1200 karakter ve 12 saniye sınırı ile mevcut sayı/ad/teknik yazım/kelime sırası korumaları
  sürer. Model hatası, zaman aşımı veya filtre reddinde ham metin kullanılır. Paragraf üretimi garantisi yoktur.
- Girdi/çıktı metni için geçici dosya veya sunucu logu üretilmez; sunucu çıktısı dosyaya kaydedilmez.
  Önceki `.local/cleanup-temp/` yolu bu akışta kullanılmaz. Mevcut aylık dikte log politikası değişmez.

## Bağlam kaynağının kapsamı

Windows'ta elle seçilen Herdr metadata kaynağı seçimden sonraki ilk Herdr diktesinin pencere hwnd/PID
kimliğine bağlanır. Tray'e tıklandığı andaki pencere esas alınmaz. Başka pencere veya Chrome'da bu kaynak
kullanılmaz; varsayılan başlık/sabit ipuçlarına dönülür. Aynı bağlı pencereye dönüşte kaynak yeniden
kullanılabilir. Aynı Herdr penceresindeki sekme değişimi algılanmaz; açık kaynak seçimi yeniden yapılmalıdır.
Uzak pane otomatik eşlenmez. Kaynak hâlâ salt okunurdur ve yapıştırma hedefi değildir.
F13 bitişinden sonra bağlam hazır bilgisi en fazla 150 ms beklenir; metadata okuması takılırsa Whisper
o tur sabit ipuçlarıyla devam eder.

## İçeriksiz süre ölçümü

`.local/metrics/dictation.jsonl` kaydı yalnız sayısal süre/uzunluk ve durum alanlarından oluşur:
bağlam bekleme, Whisper, temizlik, yapıştırma ve F13 bitişinden yapıştırmaya toplam süre. Dikte
metni, pencere başlığı, pane/proje adı ve dosya içeriği yoktur. Konuşma/kayıt süresi bu toplamın
dışındadır. Tray son diktenin süre özetini gösterir. Çıktı git dışındadır; konumu README yerel dosya
tablosuna eklenmiştir.

## Sonuçlar ve açık kabul

Nihai doğrulama:

- 61/61 test, `dictation.py`/`file_queue.py` derleme ve diff kontrolü geçti.
- Gerçek tray menüsü ve callback kontrolü 18 öğeyle geçti.
- Model ve prefix'in arka planda ilk hazır olması: 3,274 saniye.
- Kısa örnek ilk istek 1,110 saniye, sıcak istek 0,954 saniye; önceki süreç-başına örneği yaklaşık 4,3 saniyeydi.
- 208 karakter örneği 3,369 saniye; önceki süreç-başına ölçümü 6,27 saniyeydi.
- 506 karakter örneği 8,336 saniye; modelin kelime değişimi filtreyi geçmedi ve ham metin korundu.
- Dokuz çağrı: altı kabul, üç güvenli ham metne dönüş (teknik boşluk, girdi içindeki talimat, orta uzunlukta eşanlamlı kelime değişimi).
- Nihai sentetik kayıt `.local/cleanup-v3-evaluation.json` dosyasına önceki ölçümün üzerine yazıldı.
- Ana GUI `finally` kapanış yolu durdurma sinyalini ayarlar ve sahip olunan temizlik sunucusunu kapatır.
- Gerçek benchmark sonunda sahip olunan süreç ve işçi durdu; hazır durumu sıfırlandı.

Eski daemon (PID 27224) normal kapatıldı; `scripts/start.vbs` ile bağımsız başlatılan yeni daemon
(PID 14292) çalışıyor. Sahip olduğu `llama-server` PID 34376, `/health` yanıtı `status: ok` olarak
doğrulandı; çalışma kümesi 2081 MB, yaklaşık 2 GB. Bu PID'ler oturum anının kaydıdır.

Bu sentetik süreler gerçek mikrofon gecikmesi garantisi değildir. Gerçek mikrofonla kullanıcı denemesi
henüz yapılmadı.

Hazır olmama/zaman aşımı, süreç temizliği ve 150 ms bağlam sınırı otomatik/sentetik kontrollerde doğrulandı.
Gerçek mikrofon gecikmesi/kalitesi, başka pencereye geçince bağlam kaynağının bırakılması ve
telemetri/tray tutarlılığının günlük kullanım kabulü ile Mac doğrulaması açıktır. Takip
[TODO.md](../../TODO.md) içindedir. Commit/push yapılmadı.
