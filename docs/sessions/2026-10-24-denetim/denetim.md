# Kod ve güvenlik denetimi

Bu belge uygulama öncesi bulguları korur. Sonradan onaylanan düzeltmeler ve kalanlar
[uygulama kaydında](uygulama.md) belirtilmiştir.

## Kapsam ve sınır

`dictation.py`, `file_queue.py`, testler, metin başlatma/kurulum betikleri, requirements ve Git dosya
envanteri incelendi. Yerel faster-whisper/Hugging Face kaynakları ağ ve bağlam seçeneklerini doğrulamak
için okundu. Gerçek ses/transkript/log içeriği, sır dosyaları veya başka ajan oturumları okunmadı.
Mac uygulama paketi Windows'ta çalıştırılıp doğrulanmadı. Bu çalışma bağımlılıkların bütün kaynaklarının
ve CVE kayıtlarının denetimi veya canlı ağ trafiği ölçümü değildir.

## Öncelikli bulgular — düzeltme yapılmadı

1. **Yüksek: sıfırlama, işlenmekte olan diktenin gönderimini iptal etmiyor.** `dictation.py:471`
   durum ve tamponları temizliyor; `do_stop_and_send` (`:3198`) önceden aldığı sesin çözümlemesinden
   döndüğünde kayıt kimliği/iptal kontrolü olmadan pano ve Enter'a ilerliyor. Sahte transcribe içinde
   `_do_reset` çağrılan bağımsız sınamada gönderim yine gerçekleşti. Öneri: kayıt kimliği ve iptal
   kontrolünü gönderim sınırına kadar taşı; eski iş yeni kaydın durumunu değiştiremesin.
2. **Yüksek etki, mevcut kullanım tercihi: hedef pencere doğrulanmıyor.** `paste_and_send` (`:407`)
   beklemelerden sonra o anki pencereye Ctrl/Cmd+V ve Enter basıyor. İşleme sırasında odak değişirse
   başka sohbet veya terminale yazabilir. Pano önceki içeriğinin üstüne yazılır ve son metin panoda kalır.
   Öneri: kayıt başındaki pencereyi doğrula, hedef değişmişse otomatik gönderme. Bu davranış değişikliği
   ayrıca kararlaştırılmalı; uygulamanın amaçlanan otomatik Enter özelliği kendiliğinden kaldırılmamalı.
3. **Orta: aynı adlı dosyanın üstüne yazma mümkün.** `_unique_path` (`:1127`) yalnız bir kez saniye
   eki ekliyor; o yol da varsa tekrar denemiyor ve dosyayı atomik ayırmıyor. Sahte sabit saatte üçüncü
   adlandırma mevcut dosyayı döndürdü. WAV/MD yazıcıları üzerine yazabilir; paralel işler de yarışır.
   Öneri: atomik benzersiz hedef oluşturma; kaynak taşımasında da aynı koruma.
4. **Gizlilik tercihi: tam metin logları kalıcı.** `:163–200`, `:1097–1104`, `:1837`, `:3175–3236`,
   `:3295`, `:3380` dikteyi, duyulan metni ve filtrelenen parçaları loglayabilir. Bu 16 Eylül'de alınmış
   bilinçli karardır; hata diye kaldırılmadı. Wake word açıkken gönderilmeyen konuşmalar da loga girebilir.
   Dikte sesi esas olarak RAM'dedir; toplantı/Meet sesi WAV, transkript MD olarak kalır. RAM tamponu
   normal gönderim sonunda hemen temizlenmiyor. OS temp içindeki LIVE.md normal bitişte silinir,
   çökme sırasında kalabilir. Git ignore şifreleme veya yedekten dışlama değildir.
5. **Orta, yerel güven sınırı: editör açma shell kullanıyor.** `_open_in_editor` (`:1718`, `:1739`)
   Windows'ta özel editör komutunu `shell=True`, VS Code'u `cmd /c` ile açıyor. Ortam ayarı komut
   çalıştırma yetkisi taşıyor; dosya adındaki shell genişletmeleri de güvenli argüman aktarımı açısından
   incelenmeli. Öneri: komut/argümanları ayır ve özel karakterli yolları test et. Komut çalıştırma
   istismarı bu turda denenmedi; uzaktan erişilebilir servis bulunduğu anlamına gelmez.
6. **Orta: PID kilidi atomik değil.** `:110–129`, `:3580`, `:3635` kontrol ve yazmayı ayrı yapıyor;
   iki eşzamanlı başlatma modeli yükleyebilir. CLI transcribe kendisi kilit almıyor, yalnız daemon'ı
   kontrol ediyor; iki CLI de çakışabilir. PID yeniden kullanımında süreç kimliği doğrulanmıyor.
   `os.kill(pid, 0)` için bu Windows ortamındaki geçici çocuk süreç denemesinde süreç yaşamaya devam etti;
   süreç öldürme şüphesi doğrulanmış bulgu sayılmadı.

## Doğruluk ve dayanıklılık

- **Tekrar temizliği MD'ye yansımıyor:** `_finalize_segments` (`:1036`) birleştirilmiş `text` değerini
  tekilleştiriyor fakat `segments` aynı kalıyor. MD yazıcıları segmentleri kullanıyor. Üç `Eee.` örneğinde
  dönen text `Eee.`, Markdown paragrafı `Eee. Eee. Eee.` oldu. `--aggressive` de aynı ayrımdan etkilenir.
- **Final Windows çözümlemesinde önceki metin koşullaması farklı:** `quick_transcribe` açıkça
  `condition_on_previous_text=False` verirken `_transcribe_audio_path` faster-whisper kolu (`:1251`)
  vermez; MLX final kolu verir. Halüsinasyon önleme niyeti platformlar arasında tutarlı değil.
- **Hata durumunda takılma:** `do_stop_and_send` pano/yapıştırma hatalarında durumu toparlayan
  `try/finally` içermiyor; PROCESSING'de kalabilir. `do_send` toparlıyor, iki yol farklı.
- **Wake yarışları:** çift wake yolunda (`:3388`) `sm.transition` sonucu kontrol edilmeden gönderilir.
  Stop checker yalnız state değerini denetler; reset sonrası yeni kayıt başladığında eski işin
  sonucu yeni kayda ait sanılabilir. Bazı `listen_speech_detected` atamaları global bildirilmediğinden
  yerel değişkende kalır (`do_send`, `do_stop_and_send`, `stop_word_checker`).
- **Toplantı yaşam döngüsü:** final işler daemon thread'dir; tray'den çıkış onları beklemez.
  Canlı thread için 15 saniyelik bekleme dolunca işlem sürer; yeni kayıt global tamponları yeniden
  kullanabilir. Uzun kayıtta tüm ses RAM'de tutulur, dosya decode sınırı yoktur.
- **Kuyruk henüz bağlı değil:** `file_queue.py:124` mutlak herhangi bir dosyayı kabul eder; yerel
  yazıcıya güveniyor. `:149` süre sınırını tam decode'dan sonra ölçer; 64 MB sıkıştırılmış sesin RAM
  maliyetini sınırlamaz. `validate_job` dosya kaybolursa `getsize` hatasını dışarı bırakabilir ve
  `serve` döngüsü durabilir. Entegrasyondan önce izin verilen kök, decode sınırı ve yarışlar çözülmeli.
- **Uyuyan diarize yolu:** `_pick_file_and_meet_dictate` içindeki `audio_dur` yalnız iç worker'da
  tanımlı, dış MD yazımında kullanılıyor (`:2976` civarı); özellik açıldığında hata verir.
  Mac AppleScript mesajlarında ters eğik çizgi kaçışı da tam değil. Bu yol mevcut tray'den çağrılmıyor.
- **Test açığı:** 11 test yalnız kuyruk modülünü kapsıyor; ana uygulama state/gönderim/iptal ve
  dosya adlandırma yolları için regresyon testleri yok. Mac kabul listesi açık kalıyor.

## Ağ, dış girdiler ve Git

Uygulama kaynaklarında ses/metin yükleme API'si, dinleyen port, otomatik uygulama güncellemesi veya
uygulamaya ait telemetri istemcisi bulunmadı. Mikrofon, kısayollar, dosya seçici/CLI ve yerel ortam
ayarları girdi noktalarıdır. Klavye dinleyicisi kısayol/modifier takibi yapar; genel yazılan metni loglama
görülmedi. `file_queue` dosya tabanlıdır, ağ sunucusu değildir ve daemon'a bağlı değildir.

`load_model` (`:787`) Hugging Face deposundan modeli indirebilir veya metadata sorgulayabilir;
`local_files_only` verilmemiştir. Yerel `faster_whisper/utils.py:49` bunu `snapshot_download` çağrısına
taşır. Hugging Face istemcisi Python/kütüphane sürüm başlıkları ve varsa otomatik seçilen HF kimlik
bilgisini gönderebilir (`huggingface_hub/utils/_headers.py:126–200`); gerçek token varlığına bakılmadı.
Ses yüklediği görülmedi. Uyuyan speechbrain modeli de ilk çağrıda indirilir. Kurulum betikleri pip/brew
kullanır; requirements çoğunlukla yalnız alt sürüm sınırı içerir, sürüm/hash kilidi yoktur. Model revizyonu
sabitlenmemiştir. Tam çevrimdışı çalışma istenirse önbellek zorunluluğu ve açık indirme adımı ayrı karar olur.

44 commit içeren yerel erişilebilir Git geçmişinde metin dosyalarına sınırlı anahtar biçimi taraması yapıldı
(HF/OpenAI/GitHub tipik token biçimleri ve özel anahtar başlıkları); eşleşme bulunmadı. Bu bütün sır
türlerini dışlamaz. E-posta biçimi eşleşmeleri eski BMAD örnek/şablon yollarında görüldü; değerleri
rapora alınmadı ve hepsinin kurgu olduğu doğrulanmadı. Mevcut belgelerde kişi/proje adları, eski yerel
yollar ve kayıt dosya adları bulunuyor; kişisel veri bulunmadığı iddia edilemez. Gerçek transkript,
ses ve log içeriği taramaya alınmadı; ikili Mac paketi içerik bakımından doğrulanmadı.
Geçmiş temizleme veya veri silme yapılmadı. `.mcp.json` izleniyor; sunucu adları context7, filesystem,
fetch. Bunlar geliştirme araçlarıdır, dictation.py tarafından başlatılmaz.

## Doğrulama

- `venv\Scripts\python -m unittest discover -s tests -v`: 11/11 başarılı.
- `venv\Scripts\python -m py_compile dictation.py file_queue.py`: başarılı.
- AST ile yalnız ilgili fonksiyonları ayıran sahte bağımlılıklı sınamalar: reset sonrası gönderim,
  dosya çakışması ve text/segment temizliği farkı yeniden üretildi. Uygulama import edilmedi;
  mikrofon, pano, klavye, GPU ve gerçek veri kullanılmadı.
- Canlı ses doğruluğu, gecikme, Mac çalışma zamanı ve gerçek ağ trafiği henüz ölçülmedi.
