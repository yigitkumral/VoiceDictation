# 24 Ekim 2026 — Doğrulanmış konuşma bağlamı

## İstek ve değişmeyen çıktı davranışı

Kullanıcı son kullanıcı/asistan konuşmasının Whisper'a dinamik ipucu olmasını ve çalışma şeması
istedi; uygulama ile birikmiş işlerin commit/push işlemini onayladı. Commit/push ana koordinatörün
teslim adımıdır; bu belge ajanı Git teslimatı yapmaz.

Son metin hâlâ işlem bittiğinde odaktaki alana yapıştırılır. Kaynak pane'e kilitlenmiş teslimat yoktur.
Dikte sonunda otomatik Enter yoktur; Windows boşta F13 çift basış açık Enter hareketi, CUDA Qwen ve
CPU yedeği korunur. Şema [mimari.md](../../mimari.md) dosyasındadır.

## Kaynak bulma ve doğrulama

- Herdr envanterinde tek bir tam pencere başlığı eşleşmesi varsa otomatik kaynak kullanılabilir;
  genel/belirsiz başlıkta kullanıcı **Bağlam kaynağı** menüsünden makine/pane seçmelidir.
- Windows Terminal dahil uygun terminal pencereleri desteklenir. Açık seçim pencere hwnd/PID kimliğine
  bağlanır; başka pencere/Chrome'da kullanılmaz. Aynı pencere içi sekme değişimi tespit edilmez.
- Makine, pane, terminal ve `agent_session` okuma öncesi/sonrası doğrulanır. Son değişen oturum
  tahmini, ilgisiz görev taraması veya süreç argv'sinden oturum varsayımı yapılmaz.
- Yeni kanıt: Herdr `agent_session {agent, kind: id|path, value, source}` alanını destekler;
  mevcut native SessionStart hook'ları bunu verir. Önceki “session ID API'de yok” çıkarımı eksikti;
  asıl sorun eski canlı oturumun kayıtlı kimlik taşımamasıydı. Global hook değiştirilmedi.
- Bu ana oturumun `w2G:p1` pane kaynağı doğru terminal ve doğrulanmış `CODEX_THREAD_ID` üzerinden
  elle kaydedildi. Yalnız bu tam eşlemenin kaydı kullanıldı; başka oturum içeriği taranmadı.

## Modüller ve sınırlar

`context_bridge.py` standart kütüphaneyle tam oturum ID/yolu çözer, kayıt başlığı/kimliğini doğrular,
yalnız user/assistant görünür metnini seçer. En fazla 512 KiB okunur; son 300 kelime tutulur. Sistem,
araç ve alt ajan metni dışlanır. Yeni model çalıştırmaz.

`context_source.py` yerel okumayı veya mevcut SSH profili üzerinden stdin'de verilen salt okunur
exporter'ı çalıştırır; uzak kurulum/dosya yazımı yoktur. Kimlikler değişirse sonuç kullanılmaz.
İçerik RAM'de kalır; 5 saniye geçerlilik ve kısa zaman aşımı vardır, yeni konuşma logu/transkript
kopyası oluşturulmaz.

`dictation.py` yaklaşık 0,75 saniyede kaynak kontrolü ve 15 saniyede metadata envanter yenilemesi
yapar. Tray bağlam durumunu ve kelime sayısını gösterir. Dikte 150 ms'den uzun bağlam beklemez.
Whisper'a HF tokenizer ile en fazla 160 token konuşma + 40 token hotwords, toplam 200 token verilir;
223 token sınırına dayanılmaz. Mac/tokenizer yoksa muhafazakâr UTF-8 byte sınırı kullanılır.
Kaynak yoksa, kimlik değişirse veya süre dolarsa başlık/metadata/sabit ipuçlarıyla devam edilir.

## Doğrulama ve teslim

- Gerçek yerel `ContextCache` yenilemesinde `conversation` durumu, **85 kelime** ve **88 ms** ölçüldü.
  Yalnız sayaç/durum raporlandı; konuşma metni belgeye veya çıktı raporuna alınmadı.
- Nihai tam çalıştırmada **135 test: 134 başarılı, 1 atlandı**. Atlama Windows symlink yetkisine bağlıdır.
  `dictation.py`, `context_bridge.py`, `context_source.py` derleme kontrolü geçti.
- SSH exporter sentetik olarak sınandı; gerçek SSH konuşma kaynağı henüz denenmedi.
- Normal tray kapanışıyla eski daemon 32996, ebeveyn 26804 ve sunucu 41936 kapandı. `scripts/start.vbs`
  ile bağımsız yeni daemon 88512 ve sunucu 74708 başlatıldı; tray hazır, CUDA çalıştırıcısı ve sunucu
  sağlık yanıtı `ok` doğrulandı. PID'ler oturum anının kaydıdır.
- Commit/push kullanıcı onayındadır; Git teslim kimliği bu commit'in kendi belgesine yazılmayacak,
  ana teslim yanıtında verilecek.

Önceki GPU turunun test sonucu yeni konuşma bağlamı için kabul sayılmaz. Gerçek mikrofon, SSH ve
genel başlıkta kullanıcı kaynak seçimi kabulü [TODO.md](../../TODO.md) içinde açık tutulur.
