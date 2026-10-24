# 24 Ekim 2026 — Windows terminal diktesi

> **Geri çekilen prototip.** Aynı gün Yiğit tek sefer dikteye dönülmesini istedi. Aşağıdaki canlı önizleme,
> hedefe teslimat ve Claude taslak koşulları artık etkin değildir. Güncel davranış ve kabul durumu
> [sade dikte kaydındadır](../2026-10-24-sade-dikte/README.md).

## İstek ve kapsam

Windows'ta F13 ile kaydı başlatıp mevcut önizlemede geçici metni görmek, F13 ile bitirince tam kayıttan
çözülen son metni seçilen Herdr terminaline bir kez yazmak. Otomatik Enter yoktur; wake word yolu da
Enter göndermez. İlk sürüm Windows içindir; Windows mikrofonuyla Mac'teki Herdr terminalini hedefleyen
kod yolu mevcut SSH makine profillerini kullanır.

Uygulama, belge, bağımsız inceleme ve test işleri yerel Codex alt ajanlarıyla yürütüldü. Bu kayıt
uygulanan davranışı ve henüz gerçek kullanımda doğrulanmamış sınırları ayırır.

## Hedef kararı

Herdr 0.9.3 genel API'si öndeki yerel istemciyi uzak makine profili ve pane ile güvenilir biçimde
eşleyemez. Sunucunun odaktaki pane'ini yerel istemcinin hedefi saymak çok istemcili kullanımda yanlış
terminale yazabilir. Bu nedenle hedef açık seçimdir:

1. Windows tray → **Dikte hedefi** → **Terminal listesini yenile**.
2. **Yerel / …** veya uzak makine profilinin etiketi (örneğin **Mac / …**) altında pane etiketi/kimliğiyle terminali seç.
3. F13 başında makine profili, pane ve terminal kimliği bu kayıt için sabitlenir. Odak değişimi hedefi
   değiştirmez. Sonraki kayıtlarda seçim sen değiştirene veya daemon kapanana kadar korunur.

Otomatik Enter'ın kaldırılması kullanıcı isteğidir. Açık tray seçimi ise API sınırına karşı geliştirilen
ilk sürüm uygulama varsayımıdır; kullanıcı kabulü bekler.

Kaynak incelemesi Herdr'ın resmi **v0.9.3** koduna dayanır: bağlantı/makine ayrımı için
[endpoint/catalog.rs](https://github.com/herdrdev/herdr/blob/v0.9.3/src/client/endpoint/catalog.rs),
pencere başlığının kapsamı için
[window_title.rs](https://github.com/herdrdev/herdr/blob/v0.9.3/src/config/window_title.rs), CLI komutları için
[cli/pane.rs](https://github.com/herdrdev/herdr/blob/v0.9.3/src/cli/pane.rs), pane ve metin teslim API'si için
[api/panes.rs](https://github.com/herdrdev/herdr/blob/v0.9.3/src/app/api/panes.rs).
Yerel istemciden uzak pane'e güvenilir eşleme bulunamadığı sonucu bu incelemenin çıkarımıdır.

Seçim RAM'dedir; yeni ayar dosyası yazılmaz. Varsayılan **Öndeki normal pencere (Herdr dışı)** modudur.
Bu modda normal uygulamaya pano üzerinden yapıştırılır; Herdr veya tanınan terminal penceresi (Windows
Terminal, WezTerm, conhost vb.) öndeyse hedef tahmin edilmez, metin panoda kalır ve terminal seçme
bildirimi gösterilir. Herdr dışı sıradan terminale genel yapıştırma desteklenmez. Herdr içinde açıkça
seçilen normal kabuk terminali desteklenir.

## Veri ve teslimat

- Mikrofon, ses tamponu ve Whisper Windows'ta kalır. Normal modda geçici önizleme metni terminale yazılmaz.
- F13 ile durdurunca tam ses bir kez son çözümlemeden geçer. Normal pencereye pano üzerinden yapıştırılır;
  Herdr terminaline doğrudan yazılır. Başarılı normal Herdr teslimatı panoya yazmaz; başarısız veya belirsiz
  teslimatta kurtarma kopyası panoya alınır.
- Uzak hedef için mevcut, kayıtlı ve etkin Herdr SSH makine profili gerekir. Bağlantı kurulumu ve
  istemci ayarı değiştirilmez; yeni MCP, servis veya port eklenmez.
- Terminale son metin `herdr --machine <profil> pane send-text <pane> <metin>` yoluyla yazılır.
  Metin tek satıra dönüştürülür, kontrol karakterleri çıkarılır. Enter gönderilmez.
- Teslimattan önce terminal kimliği ve ajan/oturum/süreç bilgisi yeniden doğrulanır. Değişmiş süreç,
  meşgul veya engellenmiş ajan ve doğrulama hatası otomatik yazımı durdurur. Ajan olmayan terminalde
  yalnız tanınan kabuk sürecine yazılır; editör veya başka program istemine yazılmaz.
- API zaman aşımında otomatik tekrar yoktur. Metin ulaşmış olabilir; pano kurtarma bildirimi bunu
  belirtir. Yeniden yapıştırmadan önce terminal kontrol edilir.
- Önizleme metin boşken de hedefi ve durumu gösterir; sonuç/hata bildirimi yaklaşık 15 saniye kalır.
- Bağlam yalnız seçilen pane etiketi ve çalışma klasörünün son adıdır; uzak Git dalı sorgulanmaz.
  Dosya içeriği ve terminal çıktısı okunmaz. Normal pencere hedefinde Windows VS Code başlığı
  desteklenmeye devam eder.

## Onaylanan ek deney: Claude Code canlı taslak

Yiğit ikinci F13'te geçici taslağın son metinle değiştirilmesini, boş giriş ve kayıt sırasında
düzenlememe koşuluyla denemeyi onayladı. Windows Ayarlar → **Deney: Claude canlı taslak (boş giriş)**
varsayılan kapalıdır ve yalnız RAM'de tutulur. Açık Herdr hedefi Claude Code olmalı; Codex/normal kabuk
deney hedefi değildir. Wake word kapalı ve giriş normal düzenleyici modunda olmalı; Vim modu desteklenmez.

İlk 60 saniyede yaklaşık 2,5 saniyede bir veya daha yavaş, o ana kadar biriken sesin tamamı çözülür.
İlk tek satır taslağın ardından `Ctrl+E`, `Ctrl+U` ile önceki taslak temizlenir ve yenisi yazılır.
İkinci F13 bütün sesin son metnini önce panoya alır, sonra aynı taslağı değiştirir. Enter gönderilmez.
60 saniyeyi aşınca terminal taslağı donar, tam kayıt son F13'te yine çözülür; ekrandaki önizleme son
12 saniyelik sesi göstermeyi sürdürür.

F13 dışı yerel tuş veya fare tıklaması, başka pencerede bile, deneyi o kayıt için keser; başka yazma
ve silme yapılmaz. Sonuç panoya alınır, normal teslimatla sona eklenmez. API hatası/zaman aşımı da
yazmayı keser; otomatik tekrar yoktur. Reset yazılmış taslağı silmez. Uzak/başka istemci girdisi
algılanamaz; tek kullanıcı ve düzenlememe koşulu korunmalıdır. Bu koşullar bir güvence değildir.
Boş geçici çözüm atlanır; `--`, `/`, `!`, `?` veya `@` ile başlayan taslak mod değiştirme riskine karşı
yazılmaz, deney o kayıt için kesilir ve önceki taslak korunur.

Claude Code tuş davranışı `Ctrl+E` ile mantıksal satır sonuna gitmeye, `Ctrl+U` ile mantıksal satır
başına kadar silmeye dayanır. Gerçek Claude Code girişinde bu dizinin uçtan uca kabulü henüz yapılmadı.
Diğer akışlarda normal tek son metin davranışı sürer.

## Doğrulama ve açık kabul

Son doğrulama:

- `venv\Scripts\python -m unittest discover -s tests`: **86/86 test geçti**.
- `venv\Scripts\python -m py_compile dictation.py file_queue.py`: geçti.
- `git diff --check`: temiz.
- Gerçek Windows önizleme penceresi sentetik veriyle hatasız açıldı; öndeki pencere değişmedi.
- Gerçek pystray menü oluşturucusu ve hedef seçim callback'i sahte Icon ile, olay döngüsü
  başlatılmadan denendi; geçti.

Eski daemon (PID 50124) tray `WM_STOP` yoluyla normal temizliği tamamlayarak kapandı; çıkışı doğrulandı.
`scripts/start.vbs` ile bağımsız yeniden başlatılan daemon (PID 73924) tray hazır durumuna ulaştı.
Kod değişiklikleri yeniden başlatmadan önce tamamlandı. Yeniden başlatma RAM'deki hedefi ve canlı
taslak seçimini sıfırladı: kullanıcı Herdr hedefini yeniden seçmeli ve deneyi yeniden açmalı.

Mikrofon kaydı, gerçek Claude Code taslak değişimi ve gerçek SSH yazımı denenmedi; kullanıcı deneyi
bekliyor. Başarılı otomatik testler gerçek Claude girişinde tuş dizisinin çalıştığı anlamına gelmez.

- Windows'ta gerçek F13 kaydı, boş önizlemede hedef/durum ve tek son yazım kabulü bekler.
- Yerel terminalde odak değişimi, terminalin yeniden başlaması, meşgul ajan ve zaman aşımı kabulü bekler.
- Windows → Mac gerçek SSH üzerinden uçtan uca teslimat henüz doğrulanmadı.
- Mac'te çalışan daemon için yeni terminal hedefi menüsü uygulanmadı; Mac UI ve genel kabulü açık.
- Otomatik Enter olmaması hem F13 hem wake word ile gerçek kullanımda doğrulanmalı.
- Commit/push yapılmadı; bunlar için ayrı kullanıcı onayı gerekir.

Açık maddelerin takip yeri [TODO.md](../../TODO.md), kullanım açıklaması
[nasıl çalışır](../../nasil-calisir.md#windowsta-herdr-terminalini-seçme) belgesidir.
