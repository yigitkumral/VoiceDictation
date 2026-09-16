# VoiceDictation yapı sadeleştirme — 16 Eylül 2026

**Sonuç:** Bağımsız analizler ortak bir hedef yapıda birleşti; Yiğit kararlarını verdi ve P1–P4 değişiklikleri çalışma
ağacına uygulandı. P0 veri/log geçişi, çalışma zamanı kabulü ve commit'ler koordinatör ile Yiğit'in açık işidir.

## Amaç

Aylar sonraki ilk büyük bakım turunda proje yapısını sadeleştirmek, Drive'a bağlı veri yollarını repo içine almak,
Windows/macOS kurulumunu taşınabilir kılmak ve belgeleri tek kaynaklı hale getirmek. Hotkey, tray, "Diktasyon",
`--transcribe` ve çıktı davranışı korunur.

## Katılan ajanlar

| Model / ajan | Rol |
|---|---|
| Claude Fable 5.1 (`voicedictation-scope`) | Koordinasyon, rapor derleme, Yiğit kararları ve uygulama sırası |
| Claude Opus 5 [1m], xhigh (`opus-techwriter`, `opus-yapi`, `opus-yol`, `opus-ortam`) | Belge, repo, yol ve çalışma ortamı analizleri; ardından P1–P4 uygulaması |
| Codex gpt-6-astra, high | Personasız bütüncül çapraz analiz ve Paige etkisi karşılaştırması |
| Codex GPT-5 | Oturum kaydının `docs/sessions/` düzenine alınması |

## Akış

1. Dört Opus ajanı ve Astra birbirinden bağımsız analiz yaptı.
2. Koordinatör ortak bulguları [derleme.md](derleme.md) dosyasında birleştirdi.
3. Yiğit dokuz temel kararı [kararlar.md](kararlar.md) dosyasında netleştirdi.
4. Dosya sahipleri, kabul kontrolleri ve teslim sırası [plan.md](plan.md) ile belirlendi.
5. P1 kod, P2 repo hijyeni, P3 kurulum/başlatma ve P4 belge paketleri aynı çalışma ağacında uygulandı.
6. P0 veri/log geçişi, çalışma zamanı testleri ve commit onayı ayrı tamamlanacak.

## Dosya haritası

| Yol | İçerik |
|---|---|
| [kararlar.md](kararlar.md) | Yiğit'in K1–K9 kararları |
| [derleme.md](derleme.md) | Beş bağımsız analizin uzlaşı ve ayrışmaları |
| [plan.md](plan.md) | Uygulama paketleri, sahiplik, sıra ve kabul kontrolleri |
| [brifler/](brifler/) | Ortak brif; analiz, P1–P4, karşılaştırma ve oturum düzeni görevleri |
| [sonuclar/](sonuclar/) | Ajan analizleri, Paige karşılaştırması ve P3 kurulum notları |
| [arsiv/](arsiv/) | Eski Codex `AGENTS.md` kopyası |

## Kararların özeti

- Kalıcı kullanıcı verisi git dışı `data/{inbox,audio,transcripts}/`; makineye özel çalışma verisi `.local/` altındadır.
- Drive/Desktop fallback kaldırılır; yollar `dictation.py` içindeki tek repo-göreli bloktan türetilir.
- BMAD proje kopyası çıkarılır; kurulum bağımlılıkları ve başlatıcılar platformlar arasında tekleştirilir.
- README insan girişi, CLAUDE.md kısa ajan kuralları; ayrıntılı kullanım, kurulum, TODO ve tarihçe `docs/` altındadır.
- Bu klasör karar ve kanıt kaydıdır. Güncel sistem davranışının kaynağı canlı proje belgeleridir.
