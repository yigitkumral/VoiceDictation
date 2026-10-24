# 24 Ekim 2026 — Qwen CUDA ve açık F13 çift basış

## Kullanıcının onayladığı davranış

Windows'ta boşta F13'e 350 ms içinde iki hızlı basış odaktaki alana **Enter** gönderir. Bu, kullanıcının
açık gönderme hareketidir; dikte sonuna Enter eklenmez. Boşta tek basışın kayıt başlatması çift basışı
ayırt etmek için 350 ms bekler. Kayıt sırasında basış anında durdurur; işleme sırasında Enter gönderilmez.
1,25 saniye uzun basış reset ve Mac Caps Lock çift/üç basış davranışı değişmez.

Tek sefer dikte, son odaktaki alana pano yapıştırması, salt okunur bağlam ve korumalı temizlik korunur.
Canlı önizleme/terminal rewrite ve Herdr teslimatı geri dönmez. Hotkey regresyonları gerçek gönderme
yapmadan sahte tuşlarla doğrulanır; gerçek mikrofon ve alan üzerinde kullanıcı denemesi ayrıca bekler.

## Aynı Qwen modelinin GPU çalıştırıcısı

Mevcut Qwen3-1.7B-Q8_0 modeli korunur; yeni model indirilmez. Resmi llama.cpp **b11852 CUDA 13.4**
çalıştırıcısı (yaklaşık 159,9 MB) ve CUDA çalışma zamanı (yaklaşık 423,5 MB) indirme/kurulumu onaylandı.
GPU klasörü `.local/llama-cuda/`, CPU yedeği `.local/llama/` olarak kalır. Resmi asset digest'leri doğrulandı:

| Yerel arşiv | Boyut |
|---|---:|
| `.local/llama-b11852-bin-win-cuda-13.4-x64.zip` | 159945187 bayt |
| `.local/cudart-llama-bin-win-cuda-13.4-x64.zip` | 423535356 bayt |

İndirme/hash kaydı `.local/llama-cuda-download.json` dosyasındadır. `--list-devices` çıktısında CUDA0
doğrulanırsa `--device CUDA0 -ngl all` kullanılır. CUDA aygıtı yoksa veya GPU sunucusunun başlangıç,
ön ısıtma ya da çalışma zamanı API çağrısı hata verirse CPU yedeğine geçilir. Çalışma zamanı hatasında
o dikte ham metni korur; aynı istek otomatik tekrar edilmez. Menü GPU/CPU hazır durumunu gösterir,
telemetri `cleanup_backend` alanına yalnız `CPU` / `CUDA0` yazabilir.

Kalıcı alt süreç, loopback/geçici port/anahtar, 1200 karakter/12 saniye ve kabul filtresi ilkeleri sürer.
Önceki [kalıcı CPU ölçümleri](../2026-10-24-warm-cleanup/README.md) ile aynı girdi metinleri kullanıldı:

| Ölçüm | Kalıcı CPU | Kalıcı CUDA |
|---|---:|---:|
| Model/prefix ilk hazır olma | 3,274 sn | 1,692 sn |
| 60 karakter ilk istek | 1,110 sn | 0,125 sn |
| 60 karakter sıcak istek | 0,954 sn | 0,129 sn |
| 208 karakter | 3,369 sn | 0,311 sn |
| 506 karakter | 8,336 sn | 0,735 sn |

506 karakter örneği kabul filtresini geçmedi ve ham metin korundu. GPU dokuz vakada altı kabul, üç güvenli
ham metne dönüş verdi. Sonuç `.local/cleanup-gpu-evaluation.json` dosyasındadır. GPU'ya 29/29 katman
taşındı: model 1743,77 MiB, KV 224 MiB, hesaplama 54,01 MiB; ölçülen ek VRAM 2223 MiB oldu.
Gerçek mikrofonla Whisper/GPU paylaşımı ve toplam kullanıcı gecikmesi bu sentetik ölçümle doğrulanmış sayılmaz.

Whisper'ın `INITIAL_PROMPT` listesine **Qwen** ve **Qwen3** terimleri eklendi. “Güven/küven” sözcükleri
bağlam dışı ve koşulsuz olarak Qwen'e çevrilmez; dikteyi farklı anlamlı kelimelerle değiştiren sözlük
kuralı eklenmedi.

## Konuşma bağlamı — sonraki uygulama turuna devredildi

Bu turda yalnız tasarlanan son konuşma ipucu kullanıcı tarafından daha sonra uygulama için onaylandı.
Önceki API incelemesindeki “oturum kimliği yok” sonucu düzeltildi: Herdr `agent_session` alanını ve
mevcut native SessionStart kaydını destekler; eski oturumlar kayıtlı olmayabilir. Uzak tarafta ayrı
kalıcı exporter kurulması gerekmedi; yeni çözüm mevcut SSH bağlantısında salt okunur inline exporter
kullanır. Nihai mimari, sınırlar ve doğrulama yeni
[konuşma bağlamı kaydında](../2026-10-24-conversation-context/README.md) tutulur.

## Doğrulama ve teslim

GPU kurulum ve sentetik benchmark tamamlandı. Nihai tam test çalıştırmasında **92 test geçti**;
bunların 28'i gerçek tuş göndermeyen hotkey testidir. `py_compile dictation.py file_queue.py` ve
`git diff --check` geçti. Eski daemon 14292 ve CPU sunucusu 34376 normal kapandı; `start.vbs`
ile bağımsız yeni daemon 32996 başlatıldı. CUDA sunucusu 41936, `CUDA0` çalıştırma parametresi ve
`/health` yanıtındaki `ok` doğrulandı. Ekran kartında bütün uygulamaların toplam kullanımı 5913 MiB idi.
Gerçek mikrofon ve Enter
hareketinin kullanıcı denemesi [TODO.md](../../TODO.md) içinde açık tutulur. Commit/push yapılmadı.
