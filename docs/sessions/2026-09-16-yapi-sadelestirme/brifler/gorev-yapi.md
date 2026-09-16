# Görev — opus-yapi (repo ağacı ve hijyen)

Önce aynı klasördeki `ortak-brif.md` dosyasını oku; kararlar ve kurallar orada. Sonuç dosyan: `sonuc-yapi.md`.

## Odak: kökteki her öğe için karar

- Repo kökündeki **her** dosya ve klasör için tek satır: **kalsın / taşınsın (nereye) / silinsin / gitignore** + gerekçe. Özellikle: `_bmad/` (1147 dosya), `.agents/` (untracked BMAD skill aynası + `legacy-instructions/`), `.claude/`, `.codex/`, `.playwright-mcp/`, `calibration/`, `models/`, `scripts/`, `tests/`, `file_queue.py` (untracked; `dictation.py` kullanmıyor), kökteki eski `dictation.log`, `start.bat` / `start.vbs` (kök) ile `scripts/start.*` ikiliği, `.mcp.json.example`, `docs/auto-start.md`.
- **Git durumu:** untracked dosyalar (`.agents/`, `file_queue.py`, `tests/`) ve `.gitignore` değişikliği (`.local/`) — bunlar bilinçli mi, yarım kalmış iş mi? `git log` ile bağlamına bak (commit yok!). `.gitignore`'un hedef yapı için nasıl olması gerektiğini taslakla.
- **iFonzo kıyası:** iFonzo kökü 4 öğe (`CLAUDE.md`, `README.md`, `docs/`, `tools/`). VoiceDictation için benzer sadelikte **hedef ağaç taslağı** çiz: kod, belgeler, veri (transkript, ham ses, Meet girdi), yerel çalışma dosyaları (venv, model, log, geçici), betikler. Adlandırma tutarlılığı (Türkçe/İngilizce, tekil/çoğul, kısa) için tek kural.
- **BMAD sorusu:** `_bmad/` ve `.agents/skills/` bu projede gerçekten kullanılıyor mu (izler: `_bmad-output`, story/PRD dosyaları, CLAUDE.md §2)? Kullanılmıyorsa ne olmalı — bunu Yiğit'e **soru** olarak formüle et, karar verme.
- **Ölçek:** her klasörün dosya sayısı/boyutu (yalnız sayı; içerik okuma) — hangi parçalar hacimce baskın, hangileri "görsel gürültü".

Kodun iç mantığına girme; yalnız dosyaların rolünü anlamak için gerektiği kadar bak.

## Geri çağrı (bitince, tek sefer)

1. `ListAgents` aracıyla `voicedictation-67 [231d1e]` oturumunun listede olduğunu gör.
2. `SendMessage` ile `to: voicedictation-67`, mesaj: `hazir: C:\Users\yigit\Desktop\Yazilim\VoiceDictation\docs\yapi-sadelestirme-2026-09-16\sonuc-yapi.md`
3. Gönderim hata verirse yalnız şu koşulda yedek yol: `herdr agent get voicedictation-scope` çıktısında `agent_status` `idle` veya `done` ise `herdr agent prompt voicedictation-scope 'hazir: <yol>'`. `working`/`blocked` ise gönderme, pane'de bekle.

Sonra oturumu kapatma.
