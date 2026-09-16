# Görev — codex-karsilastirma (Codex, bağımsız değerlendirme: persona fark yarattı mı?)

Sonuç dosyan: aynı klasörde `karsilastirma-paige.md`. Salt okuma; başka dosya yazma.

## Bağlam

16 Eylül 2026'da beş ajan aynı ortak brifle (`ortak-brif.md`) VoiceDictation için yapı sadeleştirme analizi yaptı. Dördü **aynı model ve ayarla** çalıştı: Claude Opus 5 [1m], effort xhigh, aynı izin kipi, aynı anda başlatıldı.

| Ajan | Persona | Odak dosyası | Sonuç |
|---|---|---|---|
| `opus-techwriter` | **BMAD `tech-writer` skill'i yüklendi ("Paige")** | `gorev-techwriter.md` (belgeler, okunabilirlik, devir testi) | `sonuc-techwriter.md` |
| `opus-yapi` | yok | `gorev-yapi.md` (repo ağacı, hijyen) | `sonuc-yapi.md` |
| `opus-yol` | yok | `gorev-yol.md` (kod yolları, veri geçişi) | `sonuc-yol.md` |
| `opus-ortam` | yok | `gorev-ortam.md` (venv, model, log, başlangıç, yedek) | `sonuc-ortam.md` |
| `codex-astra-yapi` | yok (Codex gpt-6-astra, high) | `gorev-astra.md` (bütüncül) | `sonuc-astra.md` — çapraz referans |

Persona tanımı: `.claude/skills/bmad-tech-writer/SKILL.md` → `_bmad/bmm/agents/tech-writer/tech-writer.md` (oku; persona ne vaat ediyor?).

## Soru

Yiğit'in beklentisi: aynı model + aynı ortak brif → iş kalitesi aynı olmalıydı. **Persona (Paige) gerçekten fark yarattı mı?** Yarattıysa nerede görünüyor, yaratmadıysa fark neden yok?

## Değerlendirme çerçevesi

1. **Bulgu doğruluğu:** her rapordan 3–5 somut iddia seç (dosya:satır verilenler) ve kodda/repoda doğrula. Hata oranı raporlar arasında farklı mı?
2. **Benzersiz bulgular:** yalnız Paige'in bulduğu vs yalnız diğerlerinin bulduğu maddeler. Paige'in bulguları odak alanının (belgeler) doğal sonucu mu, yoksa persona bakışının ürünü mü?
3. **Öneri kalitesi:** kararlılık ("şöyle olsun, çünkü" ↔ "olabilir"), uygulanabilirlik, basitlik (Yiğit'in "aşırı karmaşıklaştırma yok" kuralı), Yiğit'e bırakılan soruların isabeti.
4. **Yazım ve yapı:** okunabilirlik, sayfa disiplini (~1 sayfa istenmişti), tablo/liste kullanımı, kanıt gösterme alışkanlığı.
5. **Odak etkisi ile persona etkisini ayır:** brifler farklıydı; Paige'e "belgeler" verildi, diğerlerine başka alanlar. Adil karşılaştırma için: Paige'in belge dışı bulguları (kurulum, başlangıç, gitignore gibi) diğerlerinin aynı konudaki bulgularıyla nasıl kıyaslanıyor? Aynı konuda yazdıkları yerlerde biçim/derinlik farkı var mı?
6. **Astra'yı referans olarak kullan:** farklı model, personasız, bütüncül brif — persona olmadan da benzer derinliğe ulaşılmış mı?

## Çıktı (`karsilastirma-paige.md`, ≤1 sayfa, Türkçe)

- **Sonuç:** Paige etkili mi — evet / hayır / kısmen — tek cümle ve gerekçe.
- **Kanıt:** madde madde, rapor adı + satır referansı ile.
- **Ölçüm tablosu:** 4 Opus raporu (+ Astra) × {doğrulanan iddia / hatalı iddia, benzersiz bulgu sayısı, kararlılık, sayfa disiplini}.
- **Öneri:** ileride bu tür analizlerde persona kullanılsın mı, hangi işlerde?

## Kurallar

- Salt okuma. Kullanıcı verisi içeriği okunmaz (transkript, ses, log içerikleri). Daemon, commit, kurulum, başka ajan yok.
- Diğer ajanlar pane'lerinde boşta; onlara mesaj gönderme.

## Geri çağrı (bitince, tek sefer)

Koordinatör bir **Claude** oturumu (`voicedictation-67`); `codex queue` kullanma.

1. `hazir: C:\Users\yigit\Desktop\Yazilim\VoiceDictation\docs\yapi-sadelestirme-2026-09-16\karsilastirma-paige.md` satırını UTF-8 bir dosyaya yaz.
2. `node C:\Users\yigit\Desktop\Yazilim\iFonzo\docs\tools-global\herdr-coordination\bridge.cjs --provider claude --to voicedictation-67 --message-file <o dosya> --from codex-karsilastirma --task paige-karsilastirma --bypass`
3. JSON sonucunu oku: `accepted`/`delivered` yeterli; `unknown` ise tekrar gönderme, pane'de bekle.
4. Köprü `error`/`refused` verirse yalnız `herdr agent get voicedictation-scope` → `idle`/`done` iken `herdr agent prompt voicedictation-scope 'hazir: <yol>'`.

Sonra oturumu kapatma; Yiğit soru sorabilir.
