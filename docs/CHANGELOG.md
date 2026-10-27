# CHANGELOG — VoiceDictation

## 27 Ekim 2026 — iFonzo adı doğru yazılır

- Whisper "iFonzo"yu bilinen marka yüzünden "iPhonezo" yazıyordu. `_WORD_CORRECTIONS` artık iPhonezo, iPhonezu, iPhonezlu, iPhone zo, iPhones o, ifonso, ayfonzo, i-fonzo biçimlerini ekini koruyarak iFonzo yapar; tek başına "iPhone", "iPhone so" ve "iPhones oldu" değişmez.
- iFonzo, sabit Whisper terim listesinin başına eklendi (liste 156/160 token). Sohbet bağlamında sabit liste gitmediği için `PERSONAL_HINTS` ("iFonzo") Whisper ipucu terimlerinin başına her zaman eklenir; sohbette "iPhone" sık geçince Whisper markaya kayıyordu.

## 27 Ekim 2026 — Sohbet bağlamından "karar:" etiketleri atılır

- ShapeEscape pane'inde Mac diktesi metne `karar:"` ekliyordu: bölüm başlarında ve kaydın sonundaki sessizlikte art arda. Sebep, Whisper ipucuna giren sohbet kuyruğundaki ajan yanıtlarının `karar: ...` satırıyla bitmesiydi; Whisper bu kalıbı kopyalıyordu. Qwen temizliği ve kabul kapısı kelime silmediği için etiket yapıştırılan metne geçiyordu.
- `context_source._snapshot` artık Whisper ipucu ve terim ipuçları kurulmadan önce `karar:`, `soru:`, `bilgi:` (büyük/küçük harf fark etmez, iki nokta zorunlu) kalıplarını siler. İki nokta olmayan "karar", "kararı" gibi kelimeler korunur. Sondaki tekrarları silen genel bir filtre Yiğit'in kararıyla eklenmedi.
- 195 Python testi geçti. Daemon yeniden başlatılana kadar eski kod çalışır.

## 25 Ekim 2026 — Mac masaüstü diktesinde Herdr pane bağlamı

- Mac'in kendi diktesinde (dört parmak/Caps Lock) pane hiç bulunmuyordu: kod Mac'te pencere başlığı almıyordu ve Erişilebilirlik API'si de Terminal için yalnız “Terminal” döndürüyor.
- Yeni yol: öndeki Terminal/iTerm başlığı Apple Events ile okunur. Herdr dış başlığındaki `<bu Mac>: <çalışma alanı>`, yerel Herdr'ın tek odaklı pane'inin alanıyla eşleşirse o pane kaynak olur. Uzak oturum, farklı alan, iki odak veya izin yoksa tahmin yapılmaz. Okuma ~0,1 sn ve kayıt başlangıcını bekletmez (ilk ses kesilmez); izleyici aynı pane'in konuşmasını RAM'de önceden ısıtır.
- Gerçek ortamda Terminal'deki odaklı pane 0,11 sn'de doğru seçildi. 194 Python testi geçti. Daemon'ın ilk Terminal diktesinde macOS Otomasyon izni ister.

## 25 Ekim 2026 — Vault dikte: MacBook pane bağlamı

- iPhone/iPad Vault diktesi Windows daemon'ına gider. Windows tanısında Windows pane'leri 30/30 sohbet bağlamı alırken MacBook pane'leri 18/18 `unavailable` kalıyordu.
- Sebep: Windows Mac'e etkileşimsiz SSH ile bağlanınca PATH `/usr/bin:/bin:/usr/sbin:/sbin` oluyor; Homebrew `herdr` (`/opt/homebrew/bin`) bulunamıyordu. Uzak okuyucu artık `~/.local/bin`, `/opt/homebrew/bin` ve `/usr/local/bin` yollarını da dener. Mac'in SSH Python'u (3.9) köprü kodunu çalıştırıyor.
- Aynı kısıtlı ortamla bu oturumun pane'i uçtan uca okundu: eski kod `unavailable`, yeni kod sohbet (300 kelime). 192 Python testi geçti. Windows ve Mac daemon'ları yeni sürümle yeniden başlatıldı.

## 25 Ekim 2026 — Mac Whisper terim listesi ve kelime düzeltmeleri

- Mac tanı kayıtları incelendi (Yiğit'in isteğiyle). Mac'te sabit terim listesi token yerine 160 byte'ta kesiliyordu; listenin yarısı Whisper'a hiç ulaşmıyordu. Bütçe artık `mlx_whisper` tokenizer'ıyla 160 token olarak ölçülüyor; tüm liste (151 token) gidiyor.
- Listeye Codex, Herdr, pane, tab, workspace, worktree, session, VoiceDictation, shard ve compact eklendi; sık kullanılanlar başa alındı. Gerçek tokenizer ile 160 token sınırını sınayan test eklendi.
- Kayıtlarda görülen hatalar için düzeltme: Herder → Herdr, Voice Daktation/Ductation → VoiceDictation, B-MED → BMAD, Tadayıcı → Tarayıcı, sohbaya → sohbete. "şart" gibi gerçek kelimeler değiştirilmez.
- Açık: Mac'te pencere başlığı alınmadığı için otomatik Herdr pane eşleşmesi hiç çalışmıyor (53 kaydın tamamı `no_pane_match`); bağlam yalnız elle kaynak seçimiyle geliyor.
- 191 Python testi geçti.

## 25 Ekim 2026 — Mac dört parmak ve durdurma tonu

- Yiğit'in isteğiyle trackpad hareketi üç parmaktan dört parmağa geçti: üç parmak günlük macOS hareketlerinde çok kullanılıyor, dört parmak dokunma kullanılmıyor. Üç ve beş parmak reddedilir; zamanlama ve hareket eşikleri değişmedi. Modül hedef parmak sayısını bildirir; eski üç parmak modülü yüklenirse log uyarısı ve menüde "Trackpad 3 parmak" görünür.
- Bitiş tonu (eski ikili tamamlanma tonu) artık metin yapıştırılınca değil, kayıt durdurulduğu anda çalar; yapıştırma sessizdir. Tek nefes wake akışında ton mesaj alındığında çalar. Toplantı ve dosya transkripti sesleri değişmedi.
- 189 Python testi ve 13 C hareket senaryosu Mac'te geçti; yeni modül derlendi. Gerçek dört parmak ve ses kabulü ayrıca izleniyor.

## 25 Ekim 2026 — Mac klavye izni ve trackpad tanısı

- Yeni başlatıcı için kullanıcı Erişilebilirlik ve Giriş İzleme izinlerini yeniden verdi. Son açılışta güvenilmeyen klavye süreci uyarısı yok; mikrofon ve trackpad hazır. Menüden çıkışın daemon, model alt süreci ve PID kaydını birlikte kapattığı gerçek Mac'te doğrulandı.
- Mac'te yapıştırmadan önce daemon'ın gerçek Erişilebilirlik izni sorgulanır. İzin yoksa metin panoda kalır, tuş gönderilmez ve sonuç `permission_denied` olur; yanlış `pasted`/başarı sesi üretilmez. Menüde son ölçüm yerine izin eksikliği görünür.
- Trackpad logları genel hareket reddi ile gerçekten üç parmak görülen hareketlerin reddini ayırır. Kuyruk gecikmesi, dolu/eski olay sayısı ve F13 öncesi/sonrası durum kaydedilir. Hareket toleransları değiştirilmedi; eski yerel modül de yüklenebilir, yeni sayaç o durumda bilinmiyor görünür.
- 189 Python testi (Mac tamamı, Windows bir ortam atlaması) ve 12 C hareket senaryosu geçti. Otomatik yapıştırmanın kullanıcı kabulü ayrıca izleniyor.

## 25 Ekim 2026 — Mac klasör geçişi

- Mac reposu `dev/` ve `.local/` düzenine geçirildi. 71 veri dosyasının ad/boyut envanteri ve 55 paket sürümü korundu; 27 paket komutu yeni ortama göre yeniden üretildi. Önceki yerel değişiklikler Git stash'te, eski ortam ve imzalı uygulama `.local/migration-20261025/` altında korundu.
- Mac'te 187 Python testi ve 12 yerel trackpad senaryosu geçti. Yeni AppleScript uygulaması derlendi ve imzası doğrulandı; Login Items yeni `.local/VoiceDictation.app` yoluna güncellendi. Eksik `CFBundleIdentifier` anahtarını oluşturacak şekilde derleme betiği düzeltildi.
- Önceki kapanışlardan kalan dört sahipsiz, yalnız bu projeye ait Qwen süreci sonlandırıldı. Cocoa çıkışından önce trackpad, tanı yazıcısı, model sunucusu ve PID kaydı açıkça kapatılıyor; hata durumunda diğer kaynakların kapanmasını sınayan test eklendi.
- Kullanıcı yeni mikrofon iznini verdi; uygulama Hazır durumuna geldi. Yeni başlatıcının Erişilebilirlik/Giriş İzleme izinleri ve gerçek dikte denemesi ayrıca doğrulanacak.

## 24 Ekim 2026 — İki ağaçta sade yerleşim

- Yiğit'in seçimiyle bütün geliştirme dosyaları `dev/` altında birleştirildi: uygulama, yerel C modülü, `scripts/`, `tests/`, `requirements.txt`. Kökteki geçiş başlatıcısı kaldırıldı; giriş `python -m dev.dictation`.
- Yerel veri ve ortam `.local/data/`, `.local/venv/` altına taşındı; `.env` yolu `.local/.env`. Windows'ta 71 veri dosyasının ad/boyut envanteri ve 66 paket sürümü korundu; ortam ikilileri, aktivasyon ve 24 paket komutu yeni yola göre üretildi. Bağımlılıklar ve Whisper CUDA aygıtı doğrulandı.
- Windows Startup kısayolu yeni VBS yoluna güncellendi, daemon yeni ortamla açıldı; sahip olunan Qwen sunucusu sağlıklı. Başlatıcıların Python önbelleği `.local/__pycache__/` altına yönlendirildi.
- Mac `.app` ikilisi Git'ten çıkarıldı; AppleScript kaynağı ve üzerine yazmayan derleme betiği `dev/scripts/` altında. Mac kurulumu ve izin geçişi henüz yapılmadı. Mevcut yedek filtresi yeni veri yolunu dışlamıyor; bu görevde yedek filtresi veya uzak yedek değiştirilmedi.

## 24 Ekim 2026 — Eski yerel artıkların temizliği

- Windows'ta kurulmuş çalıştırıcıların üç ZIP arşivi (yaklaşık 580 MiB), geri çekilmiş önizleme testleri, tamamlanan tarayıcı/köprü deneme dosyaları ve Python önbellekleri Geri Dönüşüm Kutusu'na taşındı. Çalışan modeller, veri, tanı logları ve kurulum hash kayıtları korundu. Disk alanı Geri Dönüşüm Kutusu boşaltılınca açılır.
- Test geçici klasörünün kaynak taşınmasıyla yanlışlıkla `dev/.local/` altında oluşması düzeltildi; testler repo kökündeki `.local/test-tmp/` yolunu kullanır.

## 24 Ekim 2026 — Python kaynakları dev altında

- Uygulama ve yardımcı Python modülleri `dev/` paketine taşındı. Kökteki küçük `dictation.py` başlatıcısı mevcut Windows/Mac başlatıcılarını ve CLI kullanımını korur; imzalı Mac uygulaması değişmez.
- Mac C kaynakları da `dev/mac-trackpad/` altında toplandı; ayrı `tools/` klasörü kaldırıldı. `scripts/` yalnız işletim komutları olarak korundu. README kaynak, çalışma verisi, bağımlılık ve önbellek ayrımını açıklar.
- Veri, model, log, `.env` ve sanal ortam yolları repo kökünde kaldı. Tanı sürüm özeti yeni kaynak konumlarını okur. Testler ve güncel belgeler yeni düzene uyarlandı.
- Başlatıcı yönlendirmesi, veri yolları ve kökteki `.env` yüklemesi için üç regresyon testi eklendi. Mac repo eşitlemesi bu commit sonrası ayrı adımdır.

## 24 Ekim 2026 — Trackpad aynı süreçte, Mac ses düzeltmesi

- Ayrı TP uygulaması kapatıldı; `mac_trackpad.py` + `.local/trackpad/libvdtrackpad.dylib` artık VoiceDictation sürecinde çalışıyor. Üç parmak içeride F13 işleyicisine gider, yeni Erişilebilirlik kimliği veya tuş enjeksiyonu yok. Ayarlar menüsüne Trackpad aç/kapat ve Bildirim sesini dene eklendi.
- Mac çıkışının sessizde olduğu saptandı; kullanıcı ses istediği için %25 düzey korunarak sessizlik bir kez kaldırıldı. WAV tonları değiştirilmeden NSSound ile RAM'den çalınıyor; ayrı afplay/geçici dosya yok. Gerçek macOS API'si ve worker run loop doğrulandı; başlatma hataları ve zaman aşımı loglanıyor.
- Fiziksel üç parmak basışı kabul ediliyor; yerleşme penceresi 200 ms, toplam temas 30–600 ms. Kaydırma reddi korunuyor; reddetme nedenleri içeriksiz sayaçlarla 30 saniyede bir loglanıyor. Algılayıcıda 12 sentetik senaryo, Python'da 182 test (Windows'ta bir ortam atlaması) var. Güncel sürümün ses/hareket kabulü kullanıcı denemesinde.
- Vault makine adları aynı kısa ad kuralıyla karşılaştırılıyor (`Macbook-Pro` → `macbook-pro`); birden fazla profil aynı kısa ada düşerse kaynak seçilmiyor. Windows sunucusu düzeltmeyle yeniden açıldı.

## 24 Ekim 2026 — Mac trackpad prototipi

- Depo içinde Cocoa menü çubuğu yardımcısı: dahili trackpad'de üç parmak kısa dokunuş → isteğe bağlı F13. İlk açılış yalnız gözlem; ağ veya otomatik başlangıç yok. Özel MultitouchSupport API'si kullanılıyor. Yiğit gerçek dokunuşta TP TAP gördüğünü doğruladı; iki dokunuş olay logunda görüldü. F13/izin ve diğer hareketlerle çakışma kabulü ayrı.
- Saf C algılayıcı 10 sentetik senaryoyla sınandı. Mac F13 yolu mevcut kayıt/çift Enter durum makinesine bağlandı; Caps Lock yolu korunuyor. Mac modifier takibi sağ/sol tuşları ayrı tutuyor.
- Mac'te 178 Python testi geçti; Windows'ta 177 başarılı, 1 ortam kaynaklı atlama. Mac daemon'ı F13 sürümüyle yeniden açıldı, hazır menü durumu doğrulandı.
- Gerçek kabul: Yiğit Erişilebilirlik iznini verdi, F13 modu açıldı; üç parmakla kayıt açma/bitiş ve yapıştırma çalıştı. Mac tanısı `pasted`, Whisper 413 ms, Qwen CPU 182 ms, yapıştırma 411 ms, toplam 1,01 sn; bağlam 0 kelime. Çift hareketle Enter, normal sistem hareketleriyle çakışma ve uyku dönüşü henüz fiziksel olarak doğrulanmadı. Prototip açık bırakıldı; yeni açılışta gözlem moduna döner.

## 24 Ekim 2026 — Mac dağıtımı ve doğrulama

- Apple Silicon Mac deposu güncellendi; Python 3.14.4 bağımlılıkları, derleme ve 151 test doğrulandı. Temizlik sunucusu testindeki Windows'a özgü `CREATE_NO_WINDOW` beklentisi platforma göre ayrıldı.
- Onaylı Qwen3-1.7B-Q8_0 modeli Windows'tan kopyalandı, SHA-256 eşitliği doğrulandı. Resmi llama.cpp b11852 macOS arm64 dağıtımı yalnız `.local/` altında kuruldu; Mac'te Qwen CPU, Whisper MLX kullanıyor.
- Eski daemon menüden kapatıldı, mevcut imzalı `.app` değiştirilmeden yeniden açıldı. Hazır menü durumu ve hatasız başlangıç görüldü.
- Sentetik Türkçe ses (5,16 sn): Whisper 435 ms, Qwen 358 ms, toplam 794 ms. Qwen adayı koruma denetiminde reddedildi, ham metin korundu; model istekleri ve sonuç tanı kaydına yazıldı. Gerçek Caps Lock/mikrofon/yapıştırma kabulü kullanıcı denemesine bırakıldı.

## 24 Ekim 2026 — Vault ve cihaz bazında ayrıntılı tanı

- Vault diktesi de bağlam/model girdileri, aday/son metin ve hedef pane ile tanıya bağlandı.
- Masaüstü/Vault yolu; sınırlı istemci cihaz türü, profil kimliği ve istek kimliği ayrı tutuluyor.
- Karşılaştırma kullanım yolu ve istemciye göre ayrılıyor; backend sonucu terminal teslimi sayılmıyor.
- Ham User-Agent/IP veya ses kaydı eklenmedi; eski istemciler başlıklar olmadan çalışmaya devam ediyor.
- Doğrulama: 151 test, 150 başarılı ve 1 ortam kaynaklı atlama; derleme kontrolü geçti. Daemon yeniden başlatıldı, Qwen sağlık kontrolü başarılı. Vault'un sentetik HTTPS isteği backend kaydıyla aynı istek kimliğinde eşleşti: bildirilen iPad/istemci kimliği, model promptları ve 80 karakterlik sonuç; backend 417 ms. Vault tarafı aynı istek için terminal teslimi bildirdi. Fiziksel cihaz kabulü ayrı.

Bu dosya tamamlanan önemli işlerin ve kararların kaydıdır; en yeni kayıt en üstte durur. Ayrıntı için commit kimliği verilir, tam geçmiş `git log` çıktısındadır. Açık işler [TODO.md](TODO.md) dosyasındadır.

> 16 Eylül 2026'dan önceki kayıtlarda geçen yollar tarihçedir: Drive `Records/`, `RawRecords/`, `calibration/`, `logs/`, `docs/auto-start.md`. Güncel yerler README'deki [Yerel dosyalar](../README.md#yerel-dosyalar) tablosundadır.

---

## 2026-10-24 — Vault'tan uzak dikte (iPhone/iPad, Windows sunucu)

- Yiğit'in isteğiyle Windows daemon'ı uzak dikte sunucusu oldu. iFonzo canlı ajan grafının (Vault) kart terminalindeki mikrofon düğmesi sesi tailnet üzerinden X3'e yollar. Ses aynı sıcak Whisper modeliyle ve isteğe bağlı yerel temizlikle çözülür; metin Vault'a döner ve terminale Enter olmadan yazılır. Yapıştırma ve pano kullanılmaz.
- Yeni `remote_dictation.py` yalnız `127.0.0.1:5190`'da dinler. Tek istemcisi Vault'un terminal köprüsüdür; Tailscale kimlik denetimi orada yapılır. `X-Vault-Dikte` başlığı ve Host denetimi tarayıcı sayfalarının uca doğrudan istek atmasını engeller. Ses diske yazılmaz.
- Kayıt başında Vault pane'i bildirir. Daemon o pane'in sohbet bağlamını ayrı bir RAM önbelleğinde ısıtır, yerel bağlam izleyicisini etkilemez. Ölçüm satırına `status: returned`, `source: vault` eklendi.
- Ölçüm: 6 sn Türkçe konuşmada telefonun izlediği HTTPS yolundan uçtan uca yanıt 0,6 sn sürdü (Whisper 0,2 sn, temizlik 0,15 sn). `tests/test_remote_dictation.py` eklendi; 148 test geçti.

## 2026-10-24 — Pane ve model aşamalarıyla ayrıntılı tanı

- Yiğit'in açık isteğiyle günlük `.local/diagnostics/` kayıtları eklendi. Dikte başına kaynak/sohbet, gerçek model promptları, ham/filtreli/aday/seçilmiş metin ve pano/yapıştırma penceresi ortak kimlikle ilişkilendirilir. Açık Enter ayrı olaydır; pencere içindeki hedef veya gönderilen metin tahmin edilmez.
- İçeriksiz süreler aynı dosyada kalır; `trace_id` ile tanı kaydına bağlanır, bağlam yoksa sıfır kelime yazılır. Kod özeti ve uygulama açılışı kimliği eski/yeni sürümleri ayırır. Yazma arka plandadır; ham ses ve anahtar kaydı eklenmedi.
- `scripts/compare-dictation.py --last 100` kaynak pane/makine, sürüm ve bağlam durumuna göre metin dökmeden süre/sonuç özeti verir. Yalnız yeni kullanım izlenir; eski loglar geriye dönük tamamlanmaz.
- Derleme ve 143 test tamamlandı: 142 başarılı, bir Windows symlink testi atlandı. Tanı yazıcısı, dosya/serileştirme hatası, iş parçacığı ayrımı, gerçek prompt ile kayıt eşitliği, reddedilen Qwen adayının korunması ve gruplama sentetik verilerle sınandı.

## 2026-10-24 — Dikte sesleri ve ayrıntılı HTML anlatımı

- İlk F13 basıldığı anda geçici ses kaydı başlar; kayıt artık çift basış aralığını beklemez. Tuş bırakıldıktan sonraki 250 ms yalnız başlangıç tonunu ve bağlam/wake işçisini erteler. Hızlı çift basışta geçici ses sessizce atılır; doğrulanmış aynı pencereye tek Enter gönderilir. Uzayan ikinci basış kaydı sürdürür; uzun basış/reset/odak değişimi ve eski timer yarışları sınandı. Önceki tonlar değişmedi.
- Yiğit ses farkını beğenmediği için ek durdurma tonu, Sistem Sesleri kanalı ve ses kilidi geri alındı. Başlangıç/tamamlanma tonları ve çalma yolu önceki sürümle aynı. Windows tray bağlam durumu artık durum makinesi değişmese de yenilenir ve simge açıklamasında gösterilir.
- [HTML şeması](dikte-akisi.html): dört kullanım adımı, yerel/SSH/tarayıcı/kaynak-yok senaryoları, koddan çıkarılan tam promptlar, 300 kelime → 160+40 token sınırı, kaynak ve bellek kullanımı. Ölçümler anlık/sentetik olarak etiketli; canlı telemetri değildir.
- Ses denemesindeki ek test kaldırıldı; geri alınan ses davranışı eski sürümle karşılaştırılarak doğrulandı. HTML'nin tarayıcı kontrolü aşağıdadır.
- Anında kayıt / gecikmiş ton akışında derleme başarılı; 138 testten 137 geçti, Windows symlink yetkisine bağlı bir test atlandı. Gerçek mikrofon ve işitsel kabul kullanıcı denemesini bekliyor.
- Uygulama normal kapatılıp bağımsız yeniden başlatıldı; tray ve CUDA sunucusu hazır. iFonzo HTML'yi Chrome'da açtı: dört adım, dört senaryo ve üç açılır bölüm çalışıyor, 375 px genişlikte sayfa taşmıyor. Yerel sunucu yalnız 127.0.0.1:8793 üzerinde; işitsel kontrol Yiğit ekran başına döndüğünde yapılacak.

## 2026-10-24 — Doğrulanmış konuşma bağlamı ve mimari şema

- Kullanıcı son konuşma bağlamını uygulamayı onayladı. `context_bridge.py` tam ID/yol çözümleme, rol filtresi ve 512 KiB/300 kelime sınırı; `context_source.py` yerel/SSH önce-sonra kimlik doğrulama ve 5 saniyelik RAM önbelleği sağlar. Yeni model, uzak kurulum veya konuşma kopyası yoktur.
- Herdr native SessionStart hook'larının mevcut `agent_session` alanı kullanılır; eski oturum kayıtlı olmayabilir. Genel başlıkta kaynak tahmin edilmez; tek tam başlık eşleşmesi veya açık **Bağlam kaynağı** seçimi gerekir. Yalnız user/assistant metni kullanılır, araç/sistem/alt ajan dışlanır.
- Whisper ipucu gerçek HF tokenizer ile 160 token konuşma + 40 token terim, toplam 200 token sınırındadır. Arka plan kaynak kontrolü 0,75 saniye, envanter 15 saniye; tray durum/kelime sayısı gösterir. Dikte en fazla 150 ms bağlam bekler.
- [Mimari şema](mimari.md) kaynak/çıktı ayrımını gösterir. Son odaktaki alana yapıştırma, açık F13 çift Enter ve CUDA Qwen davranışı korunur. Canlı doğrulanmış yerel kaynakta konuşma önbelleği 85 kelime/88 ms verdi; metin raporlanmadı. SSH exporter sentetik sınandı, gerçek uzak konuşma kabulü açık. Nihai kontroller [oturum kaydında](sessions/2026-10-24-conversation-context/README.md).
- Nihai 135 testin 134'ü geçti, Windows symlink yetkisine bağlı 1 test atlandı; üç modül derlendi. Eski daemon/sunucu normal kapandı; bağımsız yeni daemon tray hazır, CUDA sunucusu sağlık yanıtı `ok` ile doğrulandı. Gerçek mikrofon ve SSH konuşma kabulü kullanıcı denemesine açık.

---

## 2026-10-24 — Onaylı Windows F13 çift basış ve Qwen CUDA geçişi

- Windows boşta F13'e 350 ms içinde iki hızlı basış kullanıcının açık Enter hareketidir. Tek basış kayıt başlatmak için 350 ms bekler; kayıt sırasında durdurma anlıktır. İşleme sırasında Enter gönderilmez; 1,25 saniyelik reset ve Mac Caps Lock davranışı korunur. Dikte/wake word sonu hâlâ otomatik Enter göndermez.
- Aynı Qwen modeli için resmi llama.cpp b11852 CUDA 13.4 çalıştırıcısı ve çalışma zamanı kuruldu, asset digest'leri doğrulandı; `.local/llama-cuda/` GPU, `.local/llama/` CPU yedeğidir. CUDA0 aygıt doğrulaması ve başlangıç/ön ısıtma/API hatasında CPU dönüşü eklendi. Yeni model yoktur.
- Sentetik CUDA ölçümü: ilk hazır 1,692 sn, kısa ilk/sıcak 0,125/0,129 sn, 208 karakter 0,311 sn, 506 karakter 0,735 sn. Dokuz vakanın altısı kabul, üçü ham metne güvenli dönüş; 29/29 katman ve yaklaşık 2223 MiB ek VRAM. Dosya `.local/cleanup-gpu-evaluation.json`; ayrıntılar [oturum kaydında](sessions/2026-10-24-gpu-double-tap/README.md).
- Whisper terim ipucuna Qwen/Qwen3 eklendi; “güven/küven” gibi normal kelimeleri koşulsuz Qwen'e dönüştüren sözlük kuralı eklenmedi. 92 test ve derleme kontrolü geçti; daemon bağımsız yeniden başlatıldı, CUDA sunucusunun sağlık yanıtı doğrulandı.

---

## 2026-10-24 — Kalıcı yerel temizlik modeli ve süre ölçümü

- Qwen her dikte için yeniden yüklemek yerine başlangıçta arka plandaki `llama-server` alt sürecinde yüklenip bellekte tutulur. Yalnız loopback, geçici port ve rastgele erişim anahtarı kullanılır. Hazır değilse beklemeden ham metin; 1200 karakter, 12 saniye ve mevcut koruma filtresi sürer. Normal kapanışta yalnız uygulamanın başlattığı süreç kapatılır.
- Kalıcı temizlik akışı metin girdisi/çıktısı için dosya veya sunucu logu üretmez. Süre ölçümü `.local/metrics/dictation.jsonl` içine yalnız bağlam/Whisper/temizlik/yapıştırma/toplam süre, uzunluk ve durum yazar; metin, pencere/pane adı yoktur. Tray son süre özetini gösterir.
- Elle seçilen Herdr bağlam kaynağı seçimden sonraki ilk Herdr diktesinin hwnd/PID kimliğine bağlanır; başka pencere veya Chrome'da varsayılan bağlama dönülür, aynı pencereye dönüşte kaynak kullanılabilir. Aynı pencere içi sekme değişimi algılanmaz; kaynak yeniden seçilmelidir. Herdr teslimatı eklenmez; tek son yapıştırma ve Enter göndermeme davranışı korunur.
- 61/61 test, iki dosya derleme/diff ve 18 öğeli tray callback kontrolü geçti. Sentetik model/prefix ilk hazır olma 3,274 saniye; kısa ilk/sıcak istek 1,110/0,954 saniye, 208 karakter 3,369 saniye ölçüldü. 506 karakter örneği 8,336 saniyede filtre reddiyle ham metne döndü; dokuz çağrının altısı kabul, üçü güvenli ham metne dönüş. Nihai sonuç `.local/cleanup-v3-evaluation.json` dosyasına yazıldı. Model menüsü hazır/hazır değil/model yok durumunu gösterir, yeniden açma başlangıcı tekrar dener.
- Bağlam beklemesi en fazla 150 ms ile sınırlı. Benchmark'ta sahip olunan sunucu/işçi kapanışı ve hazır durumunun sıfırlanması doğrulandı. Daemon normal kapatılıp `start.vbs` ile yeniden başlatıldı; yeni model sunucusunun sağlık durumu `ok`, çalışma kümesi yaklaşık 2 GB. Gerçek mikrofon kabulü kullanıcı denemesini bekliyor. [Oturum kaydı](sessions/2026-10-24-warm-cleanup/README.md).

---

## 2026-10-24 — Son karar: tek sefer dikte, salt okunur bağlam ve yerel temizlik

- Yiğit'in isteğiyle canlı dikte önizlemesi, geçici çözümleme, Claude canlı taslak/rewrite ve Herdr teslimatı geri çekildi. F13 bitişinde tam ses tek Whisper turuyla çözülür, yerel temizlik açıksa uygulanır, sonuç o anda odaktaki alana pano üzerinden bir kez yapıştırılır. Wake word dahil otomatik Enter yoktur.
- Varsayılan bağlam tanınan terminal/editörün pencere başlığıdır. Windows **Bağlam kaynağı** menüsü isteğe bağlı salt okunur Herdr metadata kaynağıdır; teslimat hedefi değildir. Yerelde gerçek cwd ve Git dalı, uzakta yalnız varsa metadata dalı kullanılır; uzak pane otomatik eşlenmez.
- Yerel temizlik model/çalıştırıcı mevcutsa başlangıçta açıktır, tray'den kapatılabilir. Yeni indirme yoktur. 1200 karakter ve 12 saniye CPU sınırı; noktalama/paragraf, dolgu ve dar özdüzeltme için korumalı kabul uygulanır. Sayı/ad/teknik yazım veya anlam korunmazsa ham metne dönülür. Sekiz sentetik vakanın altısı kabul edildi; ilk yedi kısa örnekte 4,31–6,27 saniye, 487 karakterlik örnekte 11,51 saniye ölçüldü ve kelime değişimi nedeniyle ham metin korundu. Paragraf üretimi tutarsızdır.
- Sade sürümde 51/51 test, derleme ve 17 öğeli tray kontrolü geçti. Gerçek mikrofon ve Mac kabulü açık; daemon yeniden başlatma sonucu oturum kaydına eklenecek.
- Önceki canlı/terminal deneyleri aşağıda tarihçe olarak korunur; etkin kullanım kısıtları değildir. Son doğrulama ve daemon durumu [sade dikte kaydında](sessions/2026-10-24-sade-dikte/README.md) izlenir.

---

## 2026-10-24 — Onaylı deney: Claude Code canlı taslak

> Aynı gün sonraki sadeleştirme kararıyla geri çekildi; aşağıdaki davranış ve testler önceki prototipin tarihçesidir.

- Windows Ayarlar'a **Deney: Claude canlı taslak (boş giriş)** eklendi; varsayılan kapalı, seçim RAM'de. Yiğit boş/normal Claude Code girişinde, kayıt sırasında düzenleme yapmadan denemeyi onayladı. Herdr'da Claude hedefi seçilmeli ve wake word kapalı olmalı.
- İlk 60 saniyede biriken sesin tamamından çözülen tek satır taslak yaklaşık 2,5 saniyede bir yenilenir: `Ctrl+E`/`Ctrl+U` önceki taslağı temizler, yeni tam taslak yazılır. İkinci F13 tam kaydın son metnini önce panoya alır, sonra taslağın yerine yazar; Enter yoktur. 60 saniye sonrasında terminal taslağı donar, ekrandaki son 12 saniyelik önizleme sürer.
- Yerel F13 dışı tuş veya fare tıklaması ve API hatası/zaman aşımı sonraki yazma/silmeleri durdurur. Sonuç panoda kalır; normal teslimata ekleme yapılmaz. Reset yazılmış taslağı silmez. Başka istemcinin yazması algılanamaz; tek kullanıcı ve düzenlememe koşulu deneyin sınırıdır.
- Boş geçici sonuç atlanır; `--`, `/`, `!`, `?`, `@` başlangıçları mod değiştirmemek için deneyi keser. 86/86 test, derleme ve diff kontrolü geçti. Daemon normal tray kapanışıyla durdurulup `scripts/start.vbs` ile yeniden başlatıldı, yeni tray hazır durumu doğrulandı. RAM hedefi ve deney ayarı yeniden seçilmeli.
- Gerçek Claude Code girişinde tuş dizisi, mikrofon ve SSH uçtan uca kabulü açık; kullanıcı deneyi bekliyor. [Oturum kaydı](sessions/2026-10-24-terminal-dikte/README.md).

---

## 2026-10-24 — Windows terminal diktesi: açık hedef, son metin, Enter yok

> Aynı gün sonraki sadeleştirme kararıyla Herdr teslimatı geri çekildi; bu bölüm önceki prototipin tarihçesidir.

- Yiğit'in onayıyla diktenin otomatik Enter davranışı kaldırıldı; F13 ve wake word son metni yazı olarak bırakır. Kayıt boyunca geçici önizleme, bitişte tam sesle tek son çözümleme korunur.
- Windows tray'e **Dikte hedefi** eklendi: liste yenilendikten sonra yerel veya mevcut etkin SSH makine profilindeki Herdr terminali açıkça seçilir. Seçim yalnız RAM'de tutulur ve kayıt başında sabitlenir. Herdr 0.9.3 yerel istemci–uzak pane eşlemesi sunmadığından otomatik hedef tahmini yapılmaz.
- Açık tray seçimi ilk sürüm uygulama varsayımıdır; kullanıcı kabulü bekler. Başarılı Herdr teslimatı panoya yazmaz; başarısız/belirsiz teslimatta metin kurtarma için panoya alınır.
- Terminale yalnız son metin tek satır halinde, kontrol karakterleri ayıklanarak yazılır; Enter gönderilmez. Kimlik/süreç/ajan durumu yeniden doğrulanır; belirsiz teslimatta otomatik tekrar yapılmaz. Teslimat başarısız/belirsizse metin panoya alınır ve durum bildirimi gösterilir.
- Bağlam seçilen pane etiketi ve çalışma klasörünün son adıdır; uzak Git dalı sorgulanmaz. Windows önizlemesi boş metinde de hedef/durum gösterir; sonuç bildirimi yaklaşık 15 saniye kalır.
- Mikrofon ve model Windows'ta kalır; uzak hedefe yalnız son metin mevcut Herdr SSH bağlantısıyla gider. MCP, servis, port ve bağlantı ayarı eklenmedi.
- 62/62 test, `dictation.py`/`file_queue.py` derleme ve diff kontrolü geçti. Windows önizleme sentetik veriyle odağı değiştirmeden açıldı; pystray menüsü ve seçim callback'i sahte Icon ile olay döngüsü olmadan doğrulandı. Tanınan terminal pencerelerinde açık Herdr hedefi olmadan genel yapıştırma engellenir.
- Mac'te çalışan daemon için yeni hedef menüsü ve Windows → Mac gerçek SSH kabulü açık iş olarak tutuldu. Daemon yeniden başlatılmadı; commit/push yapılmadı. [Uygulama ve kabul sınırları](sessions/2026-10-24-terminal-dikte/README.md).

---

## 2026-10-24 — Belge düzeni, denetim ve dikte iyileştirmesi

- iFonzo, ShapeEscape ve Atelier'in belge/skill/MCP düzenleri karşılaştırıldı; küçük uygulama için tek TODO ve CHANGELOG korundu.
- `docs/README.md` belge sorumluluklarını tanımlar; CLAUDE.md ortak kurallar ve skill kaynağına işaret eder.
- Gelecek fikirleri korunarak TODO sadeleştirildi; üç dikte iyileştirmesi uygulama planı bekleyen işler olarak eklendi.
- Yiğit'in uygulama onayından sonra reset sonrası gönderim, hedef pencere kontrolü, pano/yapıştırma hata toparlaması ve atomik dosya adı ayırma düzeltildi. Tekrar temizliği Markdown segmentlerine de uygulanır.
- Dinamik proje/dal/dosya ipucu, tek modelle canlı geçici metin + tam sesle son tur ve varsayılan kapalı yerel metin temizliği eklendi. Menü ve kullanım ayrıntıları `nasil-calisir.md` içindedir.
- Ayrı indirme onayıyla Qwen3-1.7B-Q8_0 ve llama.cpp CPU çalıştırıcısı `.local/` altına kuruldu, hash'leri doğrulandı. Altı sentetik örnekte koruma/temizlik sınandı (yaklaşık 3–7 saniye).
- 34 test ve derleme kontrolü geçti; Windows önizleme odağı değiştirmeden açıldı. Canlı mikrofon kalite kıyası ve Mac kabulü açık, daemon yeniden başlatılmadı.
- MCP, istemci ayarı ve skill değiştirilmedi. [Denetim ve uygulama kaydı](sessions/2026-10-24-denetim/README.md).

---

## 2026-09-30 — `data/media/` + `data/raw/`: tek medya klasörü, ham çıktı ayrı

Veri düzeni üç klasöre indi. Kullanım (F13, wake word, tray menüsü, `--transcribe`, `--aggressive`, transkript biçimi) değişmedi; değişen yalnız dosyaların nereye gittiği.

### Kararlar (Yiğit)

| # | Karar |
|---|---|
| K1 | `data/inbox/` ve `data/audio/` birleşti: tek klasör **`data/media/`**. Girdi ve arşiv aynı yerdedir — elle bıraktığın kayıt da programın yazdığı WAV da orada durur. |
| K2 | Klasör adı `audio` değil `media`: içerik ses değil, `.mp4` gibi video dosyalarını da kapsıyor. |
| K3 | Program artık transkripti **`data/raw/`** klasörüne yazar (eskiden `data/transcripts/`). `data/transcripts/` elle düzeltilen kopyaların yeridir; program oraya yazmaz, yalnız klasörü oluşturur. |

### Akış

`data/media/<kayıt>` → Whisper → `data/raw/<ad>.md` → elle düzeltme → `data/transcripts/<ad>.md`

Ham dosya `data/raw/` altında dokunulmadan kalır, düzeltme kopyada yapılır. Program çıktısının elle düzeltilmiş bir dosyanın üstüne binmesi artık yapısal olarak imkânsız.

### Kod

- Yol bloğu: `INBOX_DIR` + `AUDIO_DIR` → `MEDIA_DIR`; yeni `RAW_DIR`. `_ensure_dirs` üç veri klasörünü oluşturur.
- Getter'lar: `_get_inbox_dir` + `_get_audio_dir` → `_get_media_dir`; `_get_transcripts_dir` → `_get_raw_dir`. Ölü `_get_lectures_dir` shim'i silindi.
- Dosya seçiciler (Windows tkinter x3, macOS osascript) `data/media/` klasöründe açılır.
- "Dök" akışındaki taşıma korundu ama olağan durumda artık çalışmaz: kaynak zaten `data/media/` altındaysa yerinde kalır.
- Üç MD yazan yol (toplantı kaydı, dök, Meet Dictation) ve uyuyan diarize kodu `data/raw/` klasörüne yazar.

### Taşıma

`data/audio/` → `data/media/` yeniden adlandırıldı, `data/inbox/` içindeki tek dosya (`Yigit - Mert - ShapeCosmos3D (2026-09-29 22 34 GMT+3).mp4`, 264 MB) oraya alındı ve boşalan `data/inbox/` silindi. 17 dosya, boyutlar değişmedi. Eski transkriptlerdeki `Kaynak` satırları tarihçedir; `data/audio/...` olarak kalır.

---

## 2026-09-22 — `data/raw/`: elle düzeltilen transkriptlerin ham hâli

- Yiğit kararı: elle ya da ajanla düzeltilen transkriptin düzenlenmemiş Whisper çıktısı `data/raw/` klasöründe, `data/transcripts/` ile aynı dosya adıyla tutulur. Düzeltilen dosyanın başlığına `- **Düzeltme:** …` satırı eklenir. Program bu klasörü kullanmaz; klasör elle yönetilir. README "Yerel dosyalar" tablosu ve `docs/nasil-calisir.md` "Çıktı biçimi" bölümü güncellendi.
- İlk kullanım: Google Meet'ten alınan iki kayıt (4 Temmuz ve 21 Eylül) `--transcribe` ile işlendi, elle düzeltildi, ham çıktıları `data/raw/` klasörüne kondu.
- Google Meet, Temmuz 2026'dan beri yeni kayıtları Drive'da `Google Meet/<toplantı>/` klasörüne yazıyor. Eski `Meet Recordings` klasörü Google tarafından `Google Meet/Legacy Meet Recordings` altına taşınıyor. Kayıtlar Drive'a uzantısız iner; dosya adına `.mp4` eklenmeden "Meet Dictation" dosya seçicisinde görünmez.

---

## 2026-09-16 — Yapı sadeleştirme: veri repo içine, tek yol bloğu, yeni belge seti

Aylar sonraki ilk büyük bakım turu. Proje, Yiğit'in genel düzenini yeniden yansıtsın ve MacBook'a taşınabilsin diye sadeleştirildi. Kullanım değişmedi: kısayol tuşları, "Diktasyon", tray menüsü, `--transcribe` ve çıktı biçimi aynı kaldı. Analiz ve uygulama brifleri `docs/sessions/2026-09-16-yapi-sadelestirme/` klasöründe.

### Kararlar (Yiğit)

| # | Karar |
|---|---|
| K1 | Veri klasörleri İngilizce: `data/inbox/`, `data/audio/`, `data/transcripts/`. |
| K2 | BMAD kaldırıldı: `_bmad/`, 116 `bmad-*` skill'i, `.agents/` aynası ve CLAUDE.md'deki BMAD bölümü. |
| K3 | `file_queue.py` ve `tests/` commit edildi, daemon'a bağlanmadı. Programı kullanmak git durumunu değiştirmez; tüm çalışma çıktıları ignore'lu. |
| K4 | Konuşmacı ayırma kodu yerinde ama kapalı. Model `models/` klasöründen `.local/models/` klasörüne taşındı. |
| K5 | Drive `Records/` klasörünün tamamı repoya alındı: 16 MD `data/transcripts/`, 11 ses dosyası `data/audio/` altına kopyalandı. Sayı, boyut ve hash doğrulandıktan sonra Drive'daki `Records/` klasörü (`index.md` dahil) kaldırıldı. |
| K6 | Cihazlar arası veri eşitlemesi yok; neyin nerede durduğu README'de belgelendi. |
| K7 | Loglar tam metinle tutulmaya devam ediyor, artık aylık dosyalarda: `.local/logs/YYYY-MM-<Ay>.log`. 157 günlük dosya ve kökteki Mart logu aylık dosyalarda birleştirildi; içerik silinmedi. |
| K8 | `data/inbox/` elle yönetilir. Meet akışı seçilen dosyaya dokunmaz, "dök" akışı dosyayı `data/audio/` klasörüne taşır. |
| K9 | Yeni transkriptlerde Kaynak satırı repo köküne göreli. Eski transkriptler değiştirilmedi. |

### Kod (`dictation.py`)

- Tüm yollar dosya başındaki tek blokta toplandı. İsteğe bağlı `VOICEDICTATION_DATA_DIR` değişkeni eklendi. Drive ve Masaüstü yedek yolları kaldırıldı; yazılamayan hedef artık açık hata verir.
- Dosya seçiciler `data/inbox/` klasöründe açılıyor.
- Aynı ada yazılan dosyalar artık zaman eki alıyor (`_unique_path`). Eskiden toplantı WAV'ı, toplantı MD'si ve "dök" MD'si aynı adlı dosyanın üstüne yazıyordu.
- Günlük log dönüşümünün yerini aylık log dosyası aldı.
- Drive ve Meet klasörü bilgisi kod yorumlarından ve kullanıcı mesajlarından temizlendi.

### Kurulum ve başlatma

- `requirements.txt` PEP 508 platform koşullarıyla tamamlandı: `pystray`, `Pillow`, CUDA kütüphaneleri, `rumps`, `mlx-whisper`. Temiz bir macOS kurulumunun `rumps` eksik olduğu için çökmesi sorunu kapandı.
- Windows başlatması:
  - `scripts/start.vbs` repo yolunu kendi konumundan buluyor.
  - Startup klasöründeki sabit yollu `start.vbs` kopyasının yerini `VoiceDictation.lnk` kısayolu aldı; kısayolu `setup.bat` yazıyor.
  - Kökteki `start.bat` ve `start.vbs` silindi.
- macOS `.app` betiği `path to me` ile repo yolundan bağımsız hale getirildi. Derleme adımları `docs/kurulum.md` dosyasında; Mac'te derlenecek (TODO).

### Repo ve belgeler

- **Taşınanlar:**
  - `CHANGELOG.md` ve `TODO.md` → `docs/`
  - `calibration/` → `docs/calibration/`
  - `docs/auto-start.md` içeriği → yeni `docs/kurulum.md` (eski dosya silindi)
- **Yeni belge seti:**
  - README, tek "Yerel dosyalar" tablosuyla insan girişi oldu.
  - `CLAUDE.md` 269 satırdan 80 satırın altına indi.
  - `docs/nasil-calisir.md` akışları, `docs/kurulum.md` kurulumu ve taşımayı anlatıyor.
  - Belgelerdeki kodla çelişen bilgiler düzeltildi: lecture'ın "diske yazılmaz" ifadesi, kurulum komutlarının klasörü, eksik Meet menü öğesi, başlatıcı zinciri.
- **Silinenler:**
  - `.playwright-mcp/` ve `__pycache__/`
  - Kökteki `dictation.log` (içeriği aylık loga birleştirildi)
- **Git dışına alınan:** `.codex/config.toml`. Dosyayı artık iFonzo'daki `sync-claude.py` üretiyor. `.gitignore` baştan yazıldı.
- **Arşivlenen:** `.agents/legacy-instructions/2026-09-14-agents.md`, `docs/sessions/2026-09-16-yapi-sadelestirme/arsiv/eski-agents-2026-09-14.md` olarak arşivlendi. Dosya Codex'in eski `AGENTS.md`'siydi ve `CLAUDE.md`'nin yalnız ad değişimli kopyasıydı. Özgün bilgi içermiyor; Codex 14 Eylül'den beri `CLAUDE.md`'yi doğrudan okuyor.

### Sonar notu

Sonar projesinin kaynak kayıtları (`2026-05-01_Sonar-1-Mustafa-brifing.mp4`, `2026-05-01_Sonar-2-Dogu-teknik-toplanti.mp4`, `2026-06-18_Sonar-3-Dogu-teknik-toplanti`) artık `VoiceDictation/data/audio/` altında. Sonar belgelerindeki ve kayıt yazan skill'indeki eski Drive yolu Sonar oturumunda güncellenecek (TODO).

---

## 2026-09-15 / 2026-09-14 — Codex ortak talimat ve MCP kaynağı

- `95d0684`: Codex, projenin `CLAUDE.md` dosyasını doğrudan okumaya başladı. Proje MCP kaynağı paylaşılır oldu ve `.codex/config.toml` eklendi.
- `69af2e6`: Ortak Codex köprüsünün yolu güncellendi.

---

## 2026-06-12 — Drive kayıt klasörleri birleştirildi (Sonar oturumu)

Bu değişiklik Sonar oturumunda, repo dışında yapıldı. Drive'daki `Meet Recordings\RawRecords\` klasörü `Records\RawRecords\` altına birleştirildi, boşalan klasör silindi. Sonar'ın iki Meet kaydı içeriğe uygun adlarla yeniden adlandırıldı ve Drive `Records/index.md` dosyasına Sonar referansı eklendi.

---

## 2026-06-18 — Kalibrasyon paketi 1: sesli-okuma diff'inden kelime duzeltmeleri

Yontem degisikligi: kronik Whisper transkripsiyon hatalarini gunluk log madenciligi yerine
**tek bir kalibrasyon okumasiyla** yakaladik. Kullaniciya domain jargonunu + konusma stilini
iceren ~5 paragraflik Turkce metin (`calibration/reference_tr.txt`) okutuldu; referans ↔
Whisper ciktisi karsilastirilip ~25 substitution kalibi cikarildi. WER ~%8-9, hatalar ozel
isimlerde yogunlasiyordu (bağlam kopmasinin asil sebebi).

### Yeni: `calibration/`

- **`reference_tr.txt`** — kalibrasyon okuma metni (3466 dikte log korpusu + Claude Code sohbet
  gecmisinden damitilan jargon + kullanicinin gercek cumle ritmi; her kronik hata terimi gomulu).
- **`README.md`** — kalibrasyon mantigi (jiwer diff → `_WORD_CORRECTIONS`/`hotwords` onerisi) ve
  planlanan `--calibrate` motoru akisi.

### `_WORD_CORRECTIONS` genisletildi (dictation.py)

Tek kayittan (Zugzwang) 13 kayda cikti. Hepsi `quick_transcribe → _clean_transcription` uzerinden
ana dikte akisinda aktif, geriye uyumlu:

- **Zugzwang `x` bug fix** — eski regex `[gcktsz]` "Zuxvank" varyasyonunu kaciriyordu → `[gcktsxz]`.
- **Claude/Claude Code** (clout/cloud/claud/klod), **Atelier** (ateliyer/atelyal/atelial/ateliyel),
  **VoiceDictation** (Voice Daktion/Diction/Stick), **NotebookLM**, **BMAD** (VMED), **PRD** (PDD),
  **ChatGPT** (chat GPT), **delisting** (D-Listing), **PID lockfile** (PID log file).
- **docs** — `doks`/`dox` kosulsuz → docs; `box` → docs SADECE klasor baglaminda
  (altinda/arsiv/yol/klasor), "Black Box" ve "Agent Box" lookbehind ile korunur.

25 kalip icin izole regex testi (18 duzeltme + 7 false-positive) gecti. Daemon restart ile canli.

### Acik / sonraki (16 Eylul 2026'da TODO.md'ye tasindi)

- B grubu (branch←"bir an", refactor←"reflektör", commit←"komit") regex'e uygun degil →
  `hotwords` decode-boost'u bekliyor.
- `--calibrate` motoru (jiwer ile tam otomatik diff) henuz yazilmadi.

---

## 2026-05-23 (en gec) — CLAUDE.md sadelestirme + Drive Records index + Meet Recordings manuel arsiv

### CLAUDE.md sadelestirme (315 -> 247 satir)

- Windows + macOS Auto-Start kurulum reseteleri (~70 satir) **`docs/auto-start.md`**'ye birebir tasindi; CLAUDE.md'de 5-6 satir ozet + link kaldi. Kurulum bir kez yapilan i$ oldugu icin agent'in her session'da okumasi gerekmiyordu.
- Mac'te ilk session bloguu (0.5) ~15 sat -> 5 sat'a kisaltildi; tam Mac-spesifik test checklist'i zaten TODO.md'de var (daha detayli), CLAUDE.md sadece tarih + linkle proaktif hatirlatma yapar.
- Yeni: `docs/auto-start.md` (76 sat) — Win VBScript + Mac AppleScript .app kurulum, TCC izinleri (4 zorunlu izin tablosu), stale TCC entry temizligi, `.app` yeniden olusturma snippet'i.

### Drive Records paylasimli klasor index

- Yeni dosya: **`G:\Drive'ım\Records\index.md`** — Records klasoru birden cok proje tarafindan kullanilabilen merkezi depo oldugu icin agent'lara rehber. Icinde "Klasor Sozlugu" (VoiceDictation/ + RawRecords/, hangi proje yazar), "Aktif Projeler" (su an: VoiceDictation; repo yolu + akis tablosu + Drive sabitleri), "Cross-Project Referanslar" (bos placeholder), "Agent Talimatlari" (5 maddelik kural: yeni proje, yeni klasor, cross-project read, rename, index update) var.
- `Records/RawRecords/` ile `Meet Recordings/RawRecords/` karismasin diye index'te ayrim notu — birincisi VoiceDictation'in **otomatik yazdigi** islenmis ses, ikincisi Yigit'in **elle isimlendirip tasidigi** Meet ham kayitlari (mp4 video dahil).
- VoiceDictation/CLAUDE.md §1 Modlar > Lecture Mode altina tek satir not: "Records paylasimli — yeni klasor/davranis eklerken index.md'yi de guncelle."

### Meet Recordings manuel arsiv (repo disi)

- Drive'da `G:\Drive'ım\Meet Recordings\RawRecords\` alt klasoru olusturuldu (mevcut `Records/RawRecords/` ile ayni isim/mantik, Yigit'in elle yonettigi Meet ham kayit arsivi).
- Iki bekleyen Meet kaydi yeniden isimlendirilip tasindi:
  - `trz-rjon-krk (2026-05-01 13 56 GMT) (1)` (32.5 MB, 16dk) -> **`Mustafa-Yiğit tivibu toplantısı.mp4`** (TVBuy telif hakki / korsan koruma toplantisi, Govinet firmasi)
  - `trz-rjon-krk (2026-05-01 13 56 GMT) 2` (108.2 MB, 16dk) -> **`Mustafa-Yiğit Doğu.mp4`** (TVBuy projesi kapsaminda)
- Drive Meet otomasyonu mp4'leri uzantisiz dusurdugu icin `.mp4` uzantisi manuel eklendi — Windows'ta dogru ikon + tray "🎥 Meet Dictation..." filtresine dusus icin.
- CLAUDE.md Meet Dictation alt-bolumunde "Kaynak konum" ornegi guncellendi (Meet otomasyonu -> manuel isimlendirme -> Meet Recordings/RawRecords/ pattern'i).

---

## 2026-05-23 (gec) — Meet Dictation default davranisi: diarize'siz plain dictation

Kullanici talebi: "konusmaci ayirma artik olmasin. Meets dosyalari Dictation'dan gecirilsin
ses tarafi. Goruntu tarafi varsa ellenmesin, oldugu yerde birakilsin." Diarization, gunluk
Meet transkriptlerini sabote ediyor (TODO acik is: tek-konusmaciya yapisma, yanlis kume
sayisi); cozulene kadar default sade dictation'a alindi.

### Davranis degisikligi

- Tray menusu **"🎙 Meets Dictation (konuşmacı ayır)..."** → **"🎥 Meet Dictation..."** (Win + Mac).
- Callback yeni `_pick_file_and_meet_dictate_plain()`'e baglandi. Eski diarize'li
  `_pick_file_and_meet_dictate()` (line 2612+) ve speechbrain helper'lari (line 1293-1581)
  yerinde duruyor — opt-in flag/menu item ile ileride geri acilacak. Lazy import oldugu
  icin kullanilmadigi surece speechbrain/torch/sklearn yuku yok.

### Plain Meet Dictation akisi (`_pick_file_and_meet_dictate_plain`)

1. Dosya secici: mp4/webm/mov/mkv/avi/wav/mp3/m4a/aac/flac/ogg/opus/qta.
2. Isim dialog'u: `_prompt_lecture_filename` (lecture stop ile ayni helper, default = dosya stem).
3. Audio decode: Windows/Linux `faster_whisper.audio.decode_audio` (PyAV/libav), macOS `_load_audio_via_afconvert`.
4. `_save_wav(audio, RawRecords/<isim>.wav)` — 16 kHz mono PCM, stdlib `wave` (isim cakisirsa timestamp suffix).
5. `_transcribe_audio_path(audio, beam_size=5, word_timestamps=False)` — `_finalize_segments` B1-B4 temizligi otomatik.
6. `_write_lecture_markdown(VoiceDictation/<isim>.md, ..., header="Meet Dictation — <isim>")`.
7. `_open_in_editor(md_path)` — sonuc kullaniciya gosterilir.

### Orijinal dosya politikasi (kritik fark)

`--transcribe`/"Ses dosyasini dok..." akisi orijinal dosyayi `shutil.move` ile RawRecords'a
**tasiyor**. Meet Dictation **tasimaz** — orijinal mp4 (video dahil) bulundugu konumda
(tipik: `G:\Drive'ım\Meet Recordings\`) dokunulmadan kalir. Sebep: kullanici video tarafina
sonradan tekrar bakmak isteyebilir (ekran paylasimi, slide, demo), goruntu kaybi olmasin.

### CLAUDE.md

§1 Modlar bolumune yeni "Meet Dictation" alt-baslik eklendi. Konusmaci ayirma neden simdilik
kapali, akis adimlari, orijinal dosya politikasi documente edildi.

---

## 2026-05-23 — Yeni klasor duzeni + LIVE gecici + Stop dialog + Halusinasyon paket 2

### Klasor duzeni (CLAUDE.md §1 guncellendi)

- **G Drive'da Records altinda iki klasor:**
  - `G:\Drive'ım\Records\VoiceDictation\` — MD transkriptler (lecture final + `--transcribe` ciktilari)
  - `G:\Drive'ım\Records\RawRecords\` — islenen ses dosyalari (lecture WAV dump + tasinmis dis dosyalar)
- **Drive yoksa fallback:** `~/Desktop/VoiceDictation/{VoiceDictation,RawRecords}/`
  - `_ensure_writable_dir`: `os.makedirs` + `os.access(W_OK)` testi; OSError olursa Desktop'a dus
- **Lecture mode artik RAM-only DEGIL:** kayit bitince RAM buffer `RawRecords/<isim>.wav` (16-bit PCM mono 16kHz) olarak diske dokulur.
- **`--transcribe FILE` akisi:** islem sonrasi orijinal ses dosyasi `shutil.move` ile RawRecords'a TASINIR (silinmez; isim cakisirsa timestamp suffix).
- **Eski `~/Desktop/VoiceDictation_Lectures/` deprecate:** `_get_lectures_dir()` shim olarak `_get_voicedictation_dir()`'e yonlendirir; eski cagri yollari otomatik yeni yere gider.

### LIVE pass davranisi (gecici dosya, Drive'a yazilmaz)

- LIVE transcribe pipeline **ayni kaliyor** — kullanici lecture sirasinda anlik VS Code'da takip edebiliyor.
- **LIVE.md artik `tempfile.gettempdir()/voicedictation_live/` icinde** (Windows: `%LOCALAPPDATA%\Temp\voicedictation_live\`, Mac: `/tmp/voicedictation_live/`).
- Kayit bitince **LIVE.md silinir** — sadece final MD (Drive'da) + WAV (Drive'da) kalici. WAV zaten ses orijinaline geri donus saglar, LIVE'in arsivlenmesine gerek yok.
- Yeni helper: `_get_live_temp_dir()`.

### Dosya ismi dialog (Stop'ta, cross-platform)

- Lecture kapatildiginda `_prompt_lecture_filename(default_name)` cagrilir.
  - Mac: mevcut `_prompt_lecture_filename_macos` (osascript native).
  - Windows: yeni tkinter `simpledialog.askstring` (gizli root, modal, topmost).
  - Iptal/bos -> timestamp default kullanilir.
- Dialog `_bg` background thread'inin **basinda** acilir; isim alindiktan sonra WAV ve MD direkt o isimle yazilir (eski Mac-only rename mekanizmasi kaldirildi).

### Halusinasyon fix paket 2 (B1/B2/B3/B4)

22 Mayis paket 1 (commit `b83e384`) MLX yolunda sertlestirme yapti ama Tauron Bulusma ve Yeni Kayit 21 ornek dosyalari karsilastirildiginda hala 4 acik kalip vardi:

- **B1** — Tauron LIVE'da "onun icin" x11 zincirleme tekrar. Sebep: Windows/faster-whisper `quick_transcribe` cagrisinda `condition_on_previous_text` parametresi verilmiyor (faster-whisper default'u True). MLX yolu zaten False, parite saglandi.
- **B2** — Tauron Final'da "Evet." x10 tekrar. CLAUDE.md'deki "gercek 'evet evet evet' cevaplari korunur" kurali yuzunden artifact strip yakalamiyor. Coz: opt-in agresif tekrar dedupe (`LECTURE_AGGRESSIVE_CLEANUP=False` default, `--aggressive` flag ile acilir).
- **B3** — Tauron Final'da "Hacama bu" x4 + muglak "bizemle cozum" segmentleri. Sebep: dusuk-guven (`avg_logprob` cok dusuk, `no_speech_prob` yuksek) segmentler yakalanmiyor. Coz: Whisper segment metadata'sina dayali eşik filtresi (`_drop_low_confidence_segments`, default acik).
- **B4** — Yeni Kayit 21'de "Eee" x14 filler vocalization. Coz: 3+ ardarda filler regex tekillestirme (default acik, gercek cumle-ici tekrarlari etkilemez).

Yeni helper'lar: `_drop_low_confidence_segments`, `_dedupe_repeated_segments`, `_finalize_segments`, `_FILLER_RE`.
Yeni sabitler: `LECTURE_AGGRESSIVE_CLEANUP=False`, `LECTURE_CONF_NO_SPEECH=0.6`, `LECTURE_CONF_LOGPROB=-1.0`, `LECTURE_CONF_COMPRESSION=2.4`.
Yeni CLI: `--aggressive` flag (`_run_headless_transcribe`'a aktariliyor).

Test sonucu: 92sn kayit, hicbir spam/dedupe tetiklenmedi (kayit zaten temizdi), Windows CUDA'da 92x realtime final pass.

---

## 2026-05-22 — Sessizlik halusinasyon paket 1 (commit `b83e384`)

`Hakan Hoca Risk Yonetimi 20 Mayis` lecture vakasi (70dk "Altyazi M.K." tekrari) icin uc fix:

1. **`_vad_prefilter`**: MLX yoluna Silero VAD on-filtre + `SpeechTimestampsMap` timestamp remap. iPhone 11dk kaydinda %22 sessizlik kirpildi, 0.9sn ek islem.
2. **`condition_on_previous_text=False`**: her iki MLX cagrisinda (`quick_transcribe` + `_transcribe_audio_path`) — zincirleme tekrar imkansiz.
3. **`_strip_known_artifacts`**: lecture/file post-process icin GUVENLI artifact temizleyici. `_clean_transcription`'in aksine tekrar tespiti YAPMAZ, gercek "evet evet evet" cevaplarini korur.

---

## 2026-05-22 — Meet Dictation (commit `3e11f3d`)

speechbrain ECAPA-TDNN ile konusmaci ayirma (diarization) entegrasyonu. Tray menusunden "Meet kaydi sec...". Pipeline: dekod -> VAD -> Whisper word-level -> embedding -> clustering -> isim atama -> MD.

**Bilinen sorun:** Google Meet mp4 tek-kanal mix kayitlarinda diarization bozuk (kucuk threshold tum sesi tek kumeye atiyor). Cozulmedi, TODO'da takipte.

---

## 2026-05-22 — PID lockfile (commit `c5dbc5e`)

Daemon ve headless `--transcribe` ayni anda calistiginda GPU/CUDA context cakismasi. Coz: `logs/dictation.pid` lockfile; `--transcribe` calistirilirken daemon varsa reddet, kullaniciya "once tray'den Cikis" mesaji.

---

## 2026-05-19 / 2026-05-16 — Lecture kalite tuning

- **`72a2589`**: MLX `quick_transcribe` beam_size hatasi fix + try/except guard.
- **`208578a`**: dictation ve LIVE beam_size 1 -> 3 (kalite iyilestirmesi, RTX GPU'da hiz farki yok cunku decoder yuku encoder yaninda ihmal edilebilir).
- **`367e985`**: LIVE beam=3, popup dosya isimlendirme (Mac yolunda eklenmis), MLX crash fix.

---

## 2026-04-27 — Whisper kelime duzeltmesi

`4b5de3a`: Whisper transkriptlerde "Zugzwang" gibi kelimelerin dogru yazilmasi icin `_apply_word_corrections`.

---

## 2026-04-26 — Public release + macOS test paketi

**Ana commit'ler:**
- `dcd3756`: README + CLAUDE.md macOS izin tablosu detaylandirma
- `5dd5246`: macOS test paketi — triple-tap reset (Caps Lock long-press yerine), tkinter -> osascript native picker, AppleScript .app launcher (`scripts/VoiceDictation.app`)
- `60ceb29`: Toplanti modu iyilestirmeleri (tray hiyerarsi: Toplanti/Ayarlar submenu), wake word configurable
- `d7531c8`: Editor opener cross-platform (`_open_in_editor` VS Code -> sistem default -> clipboard fallback) + Turkce lokalizasyon notu
- `a2d49db`: Public open-source hazirligi — MIT lisansi, `.mcp.json` untrack
- `3676bac`: Toplanti/ders modu — RAM-only canli transkript + dosyadan cevirme

macOS Tahoe TCC kisitlamalari nedeniyle Login Items + AppleScript .app secildi (LaunchAgent + start.sh + ad-hoc imzali shell .app denemeleri TCC tarafindan sessizce reddedildi).

---

## 2026-03-30 / 2026-03-23 — Audio buffer optimizasyon

- `3194a1c`: Wake word default kapali, listen buffer optimizasyonu, carry-over azaltma.
- `873374a`: Listen buffer ~30sn siniri (arka plan ses birikmesi onlendi).

---

## 2026-03-21 — Long-press reset + wake word toggle

- `d988f8d`: Windows'ta F13 long-press (1.25sn) kayit iptal.
- `bcb0fd0`: Anahtar kelime tray toggle.

---

## 2026-03-19 — GUI

- `c977728`: Windows GUI pystray sistem tepsisi (tkinter window'dan gecis).
- `e7dbf0a`: macOS rumps menu bar.

---

## 2026-03-17 — Audio sistem iyilestirmeleri

- `33639b6`: Halusinasyon filtresi yeniden tasarlandi — uzun metinler artik korunuyor.
- `bdb7d14`: Log rotation, audio watchdog, wake word backoff.

---

## 2026-03-15 / 2026-03-14 — Cross-platform + MLX

- `c05412a`: Halusinasyon filtresi eklendi (mlx-whisper sessizlik ciktilari).
- `ffaced8`: macOS MLX-whisper entegrasyonu, proje reorganizasyonu.
- `09928fb`: Cross-platform support, logging system, bug fixes.
- `08963d8`: Initial commit — VoiceDictation standalone project.

---

_Daha eski degisiklikler icin `git log --oneline` veya commit hash'leri ile inceleyin._
