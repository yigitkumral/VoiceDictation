# P2 — Repo hijyeni (`opus-yapi`)

Önce `plan.md` ve `kararlar.md`'yi oku (aynı klasör). Kendi analizin `sonuc-yapi.md` temel alındı. **Commit yok** (koordinatör atar). `dictation.py`, `README.md`, `CLAUDE.md`, `docs/*.md`, `requirements.txt`, `scripts/` **dokunma** (P1/P3/P4'ün). Daemon çalışıyor: `logs/` ve kök `dictation.log`'a dokunma (P0'da birleştirilecek). Drive'a dokunma.

## Yapılacaklar (sırayla)

1. **Arşiv:** `.agents/legacy-instructions/2026-09-14-agents.md` → `docs/yapi-sadelestirme-2026-09-16/eski-agents-2026-09-14.md` (taşı; P4 özünü CHANGELOG'a alacak). Sonra `.agents/` klasörünü tamamen sil (untracked ayna).
2. **BMAD çıkar (K2):** `git rm -r -q _bmad .claude/skills` (`.claude/skills/` altındaki 116 skill'in hepsi `bmad-*`; klasör boşalınca kalkar). `.claude/settings.local.json` kalır.
3. **Üretilen ayar dosyası:** `git rm --cached .codex/config.toml` (dosya diskte kalır).
4. **Taşımalar:** `git mv CHANGELOG.md docs/CHANGELOG.md`, `git mv TODO.md docs/TODO.md`, `git mv calibration docs/calibration`. `docs/auto-start.md`'ye **dokunma** (P4 içeriğini `kurulum.md`'ye aldıktan sonra kendisi siler).
5. **Yerel çöp:** kök `start.bat`, `start.vbs` (ignore'lu; Startup'taki kopya bağımsız, ona dokunma), `.playwright-mcp/`, `__pycache__/`, `tests/__pycache__/` sil.
6. **`.gitignore`** tamamen yeniden yaz (yorumlu, kısa):
   ```
   # Python
   venv/
   __pycache__/
   *.py[co]
   # Calisma ciktilari (K3: program kullanimi git durumunu kirletmez)
   data/
   .local/
   # Makineye ozel / uretilen ayarlar ve sirlar
   .env
   .mcp.json
   .codex/config.toml
   .claude/settings.local.json
   # Arac artiklari
   .playwright-mcp/
   .vscode/
   .idea/
   .DS_Store
   Thumbs.db
   ```
   Kalkan kurallar: genel `settings.json`, `logs/`, `models/`, `start.bat/vbs`, `.dictation.*`, `dictation.log`, `pretrained_models/`, `_bmad-output/`, `.env.local`. **Not:** `logs/` ve `models/` kuralları kalkınca bu klasörler P0'da taşınana kadar `git status`'ta untracked görünür — beklenen, dokunma.
7. **Codex senkronu:** `python "C:\Users\yigit\Desktop\Yazilim\iFonzo\docs\tools-global\codex\sync-claude.py" --apply` sonra aynı komut `--check`. Betik `.codex/config.toml`'u ve `.agents/skills` aynasını yeniden üretir (ikisi de git dışı). `.agents/` yeniden oluşursa `.gitignore`'a `.agents/` ekle. Çıktıyı geri çağrıda özetle.
8. **Kontrol:** `git status --short` (beklenen: staged silme/taşımalar, `.gitignore` M, `file_queue.py` + `tests/` untracked, `logs/` + `models/` untracked, `docs/yapi-sadelestirme-2026-09-16/` untracked); `git ls-files | wc -l` (hedef ≈ 25–30); `git check-ignore -v .claude/settings.local.json .codex/config.toml data/x .local/x` hepsi eşleşir.

## Geri çağrı (tek sefer)

`SendMessage` → `to: voicedictation-67`, mesaj: `hazir: P2 — <3 satır: git ls-files sayısı / sync-claude sonucu / açık nokta>`. Hata verirse yalnız `herdr agent get voicedictation-scope` `idle`/`done` iken `herdr agent prompt voicedictation-scope '<aynı mesaj>'`. Sonra pane'de bekle.
