# Görev — codex-karsilastirma: `docs/sessions/` düzeni

Yiğit kararı (16 Eylül 2026): çok ajanlı çalışma kayıtları iFonzo'daki gibi **`docs/sessions/`** altında yaşayacak. Bu turun klasörü (`docs/yapi-sadelestirme-2026-09-16/`) oraya taşınacak ve içi düzenlenecek. **Koordinatörün "başla" mesajını bekle** — P3 ve P4 ajanları bu klasöre hâlâ yazıyor/okuyor; onlar bitmeden taşıma yapılmaz.

## Yapılacaklar

1. **Örnek al:** `C:\Users\yigit\Desktop\Yazilim\iFonzo\docs\sessions\README.md` ve oradaki klasör adları (`YYYY-MM-DD-<konu>`). Aynı zihniyet, bu projeye uyarlanmış; iFonzo'nun içeriğini kopyalama.
2. **`docs/sessions/README.md`** oluştur: bu klasörün ne olduğu (çok ajanlı analiz/uygulama turlarının brif, sonuç, karar ve planları), adlandırma kuralı `YYYY-MM-DD-<konu>/`, her oturum klasöründe bir `README.md` beklentisi, oturumların listesi (şimdilik tek satır).
3. **Taşı:** `docs/yapi-sadelestirme-2026-09-16/` → `docs/sessions/2026-09-16-yapi-sadelestirme/` (klasör git'te izlenmiyor; düz taşıma). İçini düzenle — sade, az klasör:
   ```
   2026-09-16-yapi-sadelestirme/
   ├── README.md          # oturum özeti: amaç, katılan ajanlar (model/rol), akış (analiz → kararlar → plan → uygulama), dosya haritası, sonuç
   ├── kararlar.md  derleme.md  plan.md
   ├── brifler/           # ortak-brif.md, gorev-*.md (analiz + P1–P4 + karsilastirma + sessions)
   ├── sonuclar/          # sonuc-*.md, karsilastirma-paige.md, p3-kurulum-notlari.md (varsa)
   └── arsiv/             # eski-agents-2026-09-14.md
   ```
   Dosya adları değişmez. Brif dosyalarının içindeki eski mutlak yollar tarihsel kayıttır, **dokunma**.
4. **Canlı belgelerdeki referansları güncelle** (yalnız bu satırlar): `CLAUDE.md` "Araştırma kayıtları" maddesi → `docs/sessions/YYYY-MM-DD-<konu>/`; `README.md`, `docs/CHANGELOG.md`, `docs/TODO.md`, `docs/kurulum.md`, `docs/nasil-calisir.md` içinde `yapi-sadelestirme-2026-09-16` geçen yerler yeni yola. Başka içerik değişikliği yok. Kontrol: `grep -rn "yapi-sadelestirme-2026-09-16" README.md CLAUDE.md docs/*.md` boş.
5. Dokunulmayacaklar: `dictation.py`, `scripts/`, `requirements.txt`, `data/`, `.local/`, `logs/`, Drive. Commit yok.

## Geri çağrı (tek sefer)

Koordinatör Claude oturumunun adı artık **`simplify-voicedictation-structure`** (ref `231d1e`). Köprü:
`node C:\Users\yigit\Desktop\Yazilim\iFonzo\docs\tools-global\herdr-coordination\bridge.cjs --provider claude --to simplify-voicedictation-structure --message-file <utf8 dosya> --from codex-sessions --task sessions-duzeni --bypass`
Mesaj: `hazir: sessions — <yeni yol / güncellenen referans sayısı / açık nokta>`. `unknown` ise tekrar gönderme. Köprü `error`/`refused` verirse yalnız `herdr agent get voicedictation-scope` `idle`/`done` iken `herdr agent prompt voicedictation-scope '<aynı mesaj>'`.
