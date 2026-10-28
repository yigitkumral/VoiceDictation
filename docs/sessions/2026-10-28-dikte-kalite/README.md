# 28 Ekim 2026 — Dikte kalitesi

Yiğit Windows/Vault diktesinin kalitesinden memnun değildi. Bu oturum kayıt analizinden uygulamaya kadar akışı tutar.

## Akış

1. **Analiz:** 24–28 Ekim Windows tanı ve ölçüm kayıtları (449 dikte; 26–28 Ekim ayrıntılı) üç Codex GPT-6.1-Sol
   ajanına gün gün bölündü. Ham sonuçlar dikte alıntısı içerdiği için Git dışı `.local/analysis/2026-10-28-win-log/` altındadır.
2. **Çapraz görüş:** Opus 5.5 (koordinatör, kör görüş) ve Codex GPT-6-Astra medium aynı paketi bağımsız değerlendirdi; tek
   turda uzlaşıldı. Ayrışmalar: ret nedeni kaydı öne alındı, Cloud → Claude büyük harfli ürün adında uygulanmaz, ad sözlüğü
   yalnız kesin biçimlerle ayrı turda, Qwen prompt'u üç kollu çevrimdışı deneyle (Tur 4).
3. **Uygulama:** Codex GPT-6.1-Sol ajanları; Tur 1 ve Tur 2 paralel (ayrı dosyalar), Tur 3 Tur 1'in pane'inde ardışık.
   Koordinatör diff'i inceledi, belgeleri ve commit'leri yaptı.

## Dosyalar

| Dosya | İçerik |
|---|---|
| [brif-tur1.md](brif-tur1.md), [sonuc/tur1.md](sonuc/tur1.md) | Son noktalama, ret nedeni kodu, kişisel ipucu sırası, Cloud istisnası, soru işareti/tırnak kapısı, kapanış halüsinasyonu |
| [brif-tur2.md](brif-tur2.md), [sonuc/tur2.md](sonuc/tur2.md) | Whisper sohbet bağlamında Markdown ve araç çerçevesi temizliği |
| [brif-tur3.md](brif-tur3.md), [sonuc/tur3.md](sonuc/tur3.md) | Yalnız kesin ad düzeltmeleri (TestFlight, Herdr, Claude Code, push et, iFonzo) |

## Sonuç

- Uygulandı: Tur 1–3; 228 Python testi geçti. Commit'ler `8db53c9`, `2729ddd` ve Tur 3 commit'i.
- Bilinçli olarak yapılmayanlar: pane/Payne/pain, Vault/Volt, worktree, Gemini/Cemilay, Atelier'in ek almış biçimleri,
  Title Case küçültme, VAD eşiği, Qwen kapısını gevşetmek.
- **Açık — Tur 4:** yeni sürümle birikecek kayıtlarda `cleanup_reason` dağılımı görüldükten sonra Qwen prompt'u üç kolla
  (mevcut / örneksiz kısa / Qwen'siz) tanı kayıtlarındaki ham metinlerle çevrimdışı karşılaştırılacak; yararlı düzenleme,
  bozulma, gereksiz ret ve süre ölçülecek.
