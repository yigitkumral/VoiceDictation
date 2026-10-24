# Uygulama ve kabul — 24 Ekim 2026

Yiğit uygulama planını ve önerilen düzeltme kapsamını bu terminalde onayladı. Ardından Qwen3-1.7B-Q8_0
ve llama.cpp CPU çalıştırıcısının indirilmesine, sentetik Türkçe örneklerle denenmesine ayrı onay verdi.
Yiğit son teslimin ardından commit ve push için de açık onay verdi. Alt ajan kullanılmadı, alt ajana onay verilmedi.

## Uygulananlar

- Kayıt kimliği, reset sonrası eski sonucu/gönderimi ve yeni kaydın durumunun bozulmasını engeller.
  Son çözümleme ayrı thread'de çalışır; kısayol dinleyicisi iptal için açık kalır. Pano/yapıştırma
  hatasında işlem toparlanır. Tamponlar bitişte temizlenir.
- Gönderim öncesinde ve yapıştırma/Enter sınırlarında hedef kontrol edilir. Windows: HWND + PID;
  Mac: ön plandaki uygulama PID'si. Aynı pencere içindeki sekme/alan değişimi saptanmaz. İptal öncesi
  gerçekleşmiş yapıştırma geri alınmaz. Kontrol ile OS tuş olayı atomik değildir.
- `_unique_path` boş hedefi atomik `O_EXCL` ile ayırır; paralel çağrılar ve aynı saniye çakışmaları
  mevcut dosyayı seçmez. Sonraki yazım başarısız olursa boş/yarım yeni dosya kalabilir; eski dosya korunur.
- Tekrar temizliği MD'nin kullandığı segmentleri de günceller; normal anlamlı tekrarlar korunur.
- Etkin Herdr metadata'sından proje/dal/pane, Windows VS Code başlığından dosya/proje terimleri alınır.
  Mirastaki eski Herdr pane değişkenleri kullanılmaz; timeout/uyumsuz uygulama sabit ipucuna döner.
- Tek geçici çözümleme döngüsü son 12 saniyeyi işler; son tur kaydın tamamını yeniden çözer.
  Windows'ta odak almayan önizleme, Mac'te menü çubuğu/menü metni vardır. Ayarlar'dan kapatılabilir.
- Yerel temizlik varsayılan kapalıdır. Yalnız son dikte, CPU'da ayrı çevrimdışı süreçte çalışır.
  Muhafazakâr kabul filtresi ve 12 saniye timeout başarısızlıkta özgün metni korur. Genel düzeltmeleri
  tümüyle çözmez; açık gün düzeltmeleri ve dolgularla sınırlı kabul uygular.

## Doğrulama

- 34 birim/regresyon testi başarılı (11 mevcut kuyruk, 23 yeni uygulama testi).
- `py_compile dictation.py file_queue.py` başarılı. Ana uygulama import edilmeden gerçek fonksiyonlar
  AST ile ayrılarak sahte model/pano/klavye üzerinde sınandı; çalışan daemon ve GPU etkilenmedi.
- 40 paralel ad ayırma farklı hedef üretti; önceden var olan sentetik dosya aynı kaldı.
- Gerçek Windows önizleme penceresi sentetik metinle açıldı: görünürlük ve `WS_EX_NOACTIVATE` doğrulandı,
  ön plandaki pencere değişmedi. Gerçek kullanıcı ekranı/transkripti yakalanmadı.
- Yerel modelle altı sentetik örnek: `Eee bugün…` dolgusu kaldırıldı; `salı, hayır çarşamba` doğru
  düzeltildi. Sayı/tarih/isim/olumsuzluk, anlamlı tekrar ve metin içindeki emir örnekleri korundu.
  `Iıı` ile başlayan örnek muhafazakâr biçimde değişmeden kaldı. Süreler 3,17–6,89 saniye;
  uygulamanın gerçek ses gecikmesi/kalitesi ölçülmüş değildir.
- Gerçek mikrofondan önce/sonra kalite kıyası, Herdr odak eşlemesi ve Mac çalışma zamanı kabulü açık.
  Çalışan daemon yeniden başlatılmadı; değişiklikler sonraki başlatmada etkinleşir.

## Yerel model kurulumu

Model kaynağı [Qwen/Qwen3-1.7B-GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077),
Apache-2.0. Dosya `Qwen3-1.7B-Q8_0.gguf`, 1.834.426.016 bayt; hedef `.local/models/`.
SHA-256: `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`.

Çalıştırıcı [llama.cpp b11852](https://github.com/ggml-org/llama.cpp/releases/tag/b11852), MIT;
`llama-b11852-bin-win-cpu-x64.zip`, 24.173.328 bayt; arşiv `.local/` altında, içeriği `.local/llama/` altında.
SHA-256: `89d28c3d7d810a57524f4c9b13397b2485cbe32937fb302c09c1b04d2a6b3e06`.
İki dosya da yayımlanan hash ile doğrulandı. Uygulama `llama-completion.exe` kullanır; sunucu açmaz.
Sürüm/hash metadata'sı `.local/model-download.json` içindedir. Yeni cihazda aynı dosyalar doğrulanarak
kurulur; Mac için platforma uygun `llama-completion` gerekir. Uygulama bunları indirmez veya güncellemez.

## Kapsam dışında kalan denetim bulguları

PID kilidi, shell üzerinden editör açma, aylık tam metin loglama politikası, kuyruk entegrasyonu,
toplantı final thread yaşam döngüsü, uyuyan diarize hataları ve Windows dosya çözümlemesindeki
önceki metin koşullaması değiştirilmedi. [Denetim](denetim.md) tarihsel kanıttır; bu maddeler
ayrı karar/çalışma gerektirir. MCP, izin/hook ve istemci ayarları değiştirilmedi.
