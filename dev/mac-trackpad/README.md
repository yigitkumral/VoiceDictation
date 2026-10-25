# Mac trackpad özelliği (deneysel)

Trackpad algılayıcısı **VoiceDictation'ın kendi sürecinde** çalışır. Ayrı uygulama, menü
çubuğu simgesi veya Erişilebilirlik izni yoktur. Mevcut VoiceDictation mikrofon ve
yapıştırma izinleri geçerlidir. Dört parmak hareketi içeride F13 işleyicisini çağırır (üç parmak günlük macOS hareketlerinde çok kullanıldığı için seçilmedi);
işletim sistemine sahte tuş gönderilmez.

## Kurulum ve kullanım

Mac'te repo kökünde `bash dev/scripts/build-mac-trackpad.sh` çalıştırılır; yalnız
`.local/trackpad/libvdtrackpad.dylib` ve sentetik test ikilisi üretilir. VoiceDictation
normal menüsünden kapatılıp açılınca modül yüklenir ve trackpad etkin başlar.
Modül yoksa dikte normal çalışır, trackpad menüsünde kurulu olmadığı görünür.

**VoiceDictation → Ayarlar → Trackpad** aç/kapatır ve dokunuş sayısını gösterir.
Ayar o çalıştırma boyunca geçerlidir. **Bildirim sesini dene** başlangıç tonunu çalar.
Yeni modül ayrı inode'a derlenir; çalışan süreçteki modül ancak yeniden açılışta değişir.
Eski TP prototip uygulaması kullanılmaz ve başlatılmamalıdır; eski üretim dosyaları
`.local/trackpad/` altında kalabilir, otomatik başlatıcısı yoktur.

## Hareket

Tanı kayıtlarında `4_parmak_red` yalnız gerçekten dört parmak görülen hareketlerin reddini sayar; genel `red` normal tek parmak kullanımını da içerir. `kuyruk_dolu` ve `kuyruk_eski` kaybolan olayları, `F13 durum=...` ise algılanan dokunuşun uygulamada hangi duruma geçtiğini gösterir. Bu sayaçlar koordinat veya konuşma metni içermez. Yeni sayaç için yerel modül yeniden derlenir; eski modülde değer bilinmiyor olarak yazılır. Eski (üç parmak) modül yüklenirse logda uyarı çıkar ve menüde "Trackpad 3 parmak" görünür; `build-mac-trackpad.sh` ile yeniden derlenir.

- Dahili trackpad'e dört parmağı 200 ms içinde yerleştir, 30–600 ms toplam sürede kaldır.
- Hafif dokunma ve fiziksel sol tıklama kabul edilir. Her parmak başlangıca göre normalize
  0,035'ten fazla yer değiştirirse kaydırma/sürükleme sayılıp reddedilir.
- İki/üç/beş parmak, uzun temas, değişen parmak kimliği, sağ tıklama ve modifier ile temas reddedilir.
- Parmakların tamamı kalkınca **bir** F13 işlenir. Kayıt dokunma başlangıcında değil, sonunda başlar.
- Tek hareket kayıt açar/kapatır. Boşta iki kabul edilen hareketin arasındaki süre 250 ms'yi
  aşmazsa Enter gönderilir; dikte bitişinde otomatik Enter yoktur. Trackpad uzun basışı reset değildir.
- Eski Caps Lock çift/üçlü basışları korunur. F13, bekleyen Caps Lock toggle'ını iptal eder.

Sistem hareketleri engellenmez. Dört parmak kaydırma (Mission Control, uygulama geçişi) hareket
eşiğiyle reddedilir; kısa dokunmanın macOS ayarlarıyla çakışmadığı ayrıca sınanmalıdır. Mac odak koruması uygulama PID'si düzeyindedir; aynı uygulama
içindeki pencere/pane değişimi ayırt edilmez.

## Ses

Bildirimler aynı WAV tonlarıyla `NSSound` üzerinden RAM'den çalınır; geçici dosya veya
ayrı `afplay` süreci yoktur. Worker run loop sesin tamamlanmasını işler. Başlatma hatası
ve zaman aşımı `[SES]` olarak loglanır. Sistem sessizliği normal olarak korunur;
24 Ekim canlı düzeltmesinde kullanıcı ses istediği için Mac'in sessiz modu bir kez kaldırıldı.

## Veri, test ve bakım

`dev/mac_trackpad.py` sınırlı kuyrukla C callback'ini F13 worker'ına bağlar. 200 ms'den eski
ve kapatılmış hareketler çalıştırılmaz. Koordinatlar RAM'de işlenir; ağ, telemetri,
ekran veya klavye içeriği kaydı yoktur. Mevcut aylık loga kabul edilen hareketler ve
30 saniyelik frame/tap/red sayaçları yazılır (hareket, parmak, süre, modifier, geç yerleşme, veri).

`Gesture.h` / `test_gesture.c`: 13 sentetik senaryo. Python testleri Mac F13 durum
makinesini, modül yaşam döngüsünü, kapatmayı ve ses hatalarını sınar. Gerçek hareket,
Enter, ses ve uyku dönüşü ayrıca denenir.

**Özel API:** MultitouchSupport Apple tarafından belgelenmiş kararlı sözleşme değildir;
macOS güncellemelerinde yeniden doğrulanmalıdır. Yerel dylib daemon içinde olduğundan
ABI uyumsuzluğu daemon'ı da etkileyebilir; trackpad'i kapatmak veya modülü kurmamak mümkündür.
Yalnız ABI bildirimleri incelendi; üçüncü taraf uygulama/kütüphane depoya alınmadı:

- [ABI alanları ve callback imzası](https://github.com/asmagill/hs._asm.undocumented.touchdevice/blob/master/MultitouchSupport.h)
- [OpenMultitouchSupport ve özel framework sınırı](https://github.com/Kyome22/OpenMultitouchSupport)
