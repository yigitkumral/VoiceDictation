# 24 Ekim 2026 — Sade dikteye dönüş

## Son kullanıcı kararı

Canlı önizleme, geçici metin ve terminal taslağı yerine özgün tek sefer dikte akışı istendi:

`F13 bitişi → tam sesle tek Whisper → açıksa yerel temizlik → pano → o an odaktaki alana yapıştır`

Otomatik Enter gönderilmez; wake word yolu da Enter göndermez. Canlı dikte önizlemesi, geçici çözümleme,
Claude taslağını `Ctrl+E`/`Ctrl+U` ile değiştirme ve Herdr'a doğrudan teslimat kaldırıldı. Boş Claude
girişi, düzenleme yapmama, tek istemci ve 60 saniyelik canlı taslak sınırı artık kullanım koşulu değildir.
Önceki deney kaydı [tarihçe olarak korunur](../2026-10-24-terminal-dikte/README.md).

## A — Salt okunur bağlam

Varsayılan olarak tanınan terminal/editörün kayıt başındaki pencere başlığından kısa terimler alınır.
Başlık bir çalışma klasörü veya gerçek dal bilgisi gibi yorumlanmaz. Dosya ve terminal içeriği okunmaz.
Windows'ta **Bağlam kaynağı** menüsünden isteğe bağlı Herdr pane metadata kaynağı seçilebilir; seçim
yalnız Whisper ipucudur, yapıştırmayı yönlendirmez. Sonuç her zaman işlem bitimindeki odaktaki alana gider.

Herdr pane etiketi ve cwd'nin son adı kullanılır. Doğrulanmış yerel klasörde salt okunur Git sorgusu kısa
dalı verebilir; uzakta yalnız mevcut metadata'daki `git_branch` kullanılır. Uzak yol için yerel Git veya
uzak komut çalıştırılmaz. Yerel istemciden uzak pane otomatik eşlenmez. Seçim RAM'dedir; yeniden
başlatınca varsayılan kaynağa dönülür. Başlık/metadata yoksa veya okuma başarısızsa sabit terimler kullanılır.

## C — Yerel metin temizliği

Model ve çalıştırıcı mevcutsa başlangıçta açıktır, eksikse kapalıdır. Kullanıcı tray'den kapatabilir;
seçim RAM'dedir, sonraki başlangıçta dosyalar mevcutsa yine açılır. Yeni model/çalıştırıcı indirilmez.
Mevcut Qwen3-1.7B-Q8_0 ve llama.cpp CPU kurulumu kullanılır.

- En fazla 1200 karakter; daha uzun metin modele verilmez.
- Dört CPU thread'i, Windows'ta düşük öncelik, tur başına 12 saniye süre sınırı ve çevrimdışı çalışma.
- Noktalama, paragraf, büyük/küçük harf, ses dolgusu ve açık gün özdüzeltmesi için dar kapsam.
- Sayı/tarih, özel ad, URL/yol/kod gibi teknik literal, kelime sırası, olumsuzluk ve anlamlı tekrar
  koruması; kabul kontrolü geçmezse ham Whisper metni kullanılır.
- Paragraf üretimi tutarlı değildir. Daha genel özdüzeltmeler muhafazakâr filtreyi geçmeyebilir.
- Sekiz sentetik vakanın altısında sonuç kabul edildi. İlk yedi kısa örnekte (yaklaşık 200 karaktere
  kadar) 4,31–6,27 saniye, 487 karakterlik örnekte 11,51 saniye ölçüldü. Uzun örnekte model kelime
  değiştirdiğinden ham metin korundu. Gerçek mikrofon kalitesi ve gecikmesi bu ölçümle doğrulanmış sayılmaz.

Girdi `.local/cleanup-temp/` altında geçici tutulur; model/süreç normal bitince silinir, çökmede kalabilir.
Sentetik ölçüm `.local/cleanup-v3-evaluation.json`, eski test arşivi `.local/rejected-prototypes/`
altındadır. Bunlar git dışıdır; kullanıcı transkript/ses/log içeriği bu belge işi için okunmadı.

## Doğrulama ve teslim durumu

Sade sürümün doğrulaması:

- `venv\Scripts\python -m unittest discover -s tests`: **51/51 test geçti**.
- `venv\Scripts\python -m py_compile dictation.py file_queue.py`: geçti.
- Tray'in 17 öğeli menü kontrolü: geçti.

Eski daemon tepsi kapanış mesajıyla normal kapatıldı; `scripts/start.vbs` üzerinden terminalden bağımsız
yeniden başlatıldı. Yeni PID 27224 ve modele/ses akışına başlangıçtan sonra oluşturulan tepsi pencereleri
doğrulandı. Önceki prototipin 86 test sonucu bu sürüm için kabul sayılmaz.
Gerçek mikrofonla F13/wake/reset, son odaktaki alana tek yapıştırma, Enter olmaması ve yerel temizlik
kalitesi hâlâ [TODO.md](../../TODO.md) içindeki kabul işleridir. Mac doğrulaması ayrıca açıktır.

Commit/push yapılmadı. Yeni servis, port, MCP veya bağlantı ayarı gerekmez.
