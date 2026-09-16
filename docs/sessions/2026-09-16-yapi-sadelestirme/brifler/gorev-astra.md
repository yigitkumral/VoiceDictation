# Görev — codex-astra-yapi (Codex Astra, bağımsız tam analiz)

Önce aynı klasördeki `ortak-brif.md` dosyasını oku; kararlar ve kurallar orada. Sonuç dosyan: `sonuc-astra.md`.

## Odak

Bağımsız ve bütüncül bir bakış: repo ağacı, koddaki dosya-sistemi yolları, yerel bağımlılıklar (venv, model önbelleği, log, başlangıç), belgeler. iFonzo'nun üst düzey düzeniyle karşılaştır. Çıktı olarak **tek bir hedef yapı önerisi** ver (klasör ağacı taslağı + her klasörün tek cümlelik amacı) ve Drive'dan repo içine geçiş için analiz düzeyinde adımları listele (uygulama yok).

Özellikle görüşünü istediğimiz noktalar:
- Veri (transkript + ham ses) repo içine gelince adlandırma ve yerleşim; Meet için elle bırakılan girdi klasörü nasıl olsun.
- Yol yönetimi nasıl **basit** kalır (tek yerde tanım, Windows/Mac parity, env override gerekli mi, Drive fallback mantığı artık gereksiz mi).
- Kökteki yardımcı klasörler (`_bmad`, `.agents`, `.claude`, `.codex`, `calibration`, `models`, `scripts`, `tests`) ve `file_queue.py` hakkında kararın.
- MacBook'a taşınmada neyin kopyalanacağı, neyin yerinde yeniden üretileceği.

Diğer ajanlar (Claude Opus) paralel çalışıyor; onların dosyalarını okuma, kendi yargınla yaz.

## Geri çağrı (bitince, tek sefer)

Koordinatör bir **Claude** oturumu; `codex queue` kullanma. Kısa mesaj köprüsünü kullan:

1. `hazir: C:\Users\yigit\Desktop\Yazilim\VoiceDictation\docs\yapi-sadelestirme-2026-09-16\sonuc-astra.md` satırını UTF-8 bir dosyaya yaz (örn. sistem temp altına).
2. Çalıştır:
   `node C:\Users\yigit\Desktop\Yazilim\iFonzo\docs\tools-global\herdr-coordination\bridge.cjs --provider claude --to voicedictation-67 --message-file <o dosya> --from codex-astra-yapi --task yapi-sadelestirme --bypass`
3. Sonucu **JSON çıktısından** oku: `accepted`/`delivered` yeterli. `unknown` ise **tekrar gönderme**, pane'de "geri çağrı belirsiz" yaz ve bekle.
4. Köprü hata verirse (`error`, `refused`) yalnız şu koşulda yedek yol: `herdr agent get voicedictation-scope` çıktısında `agent_status` `idle` veya `done` ise `herdr agent prompt voicedictation-scope 'hazir: <yol>'`. `working`/`blocked` ise gönderme, pane'de bekle.

Sonra oturumu kapatma; Yiğit soru sorabilir.
