# VoiceDictation yapı sadeleştirme — uygulama planı (onaylı, 16 Eylül 2026)

Kaynak: `~/.claude/plans/tender-bouncing-owl.md` — Yiğit onayladı. Kararlar: `kararlar.md`. Analiz: `derleme.md`.

**Değişmezler:** kullanım aynı kalır (F13 / Caps Lock x2, "Diktasyon", tray menüsü, `--transcribe`, çıktı biçimi); `dictation.py` tek dosya kalır; venv'e dokunulmaz; kullanıcı verisi içeriği okunmaz; her commit Yiğit onayıyla; daemon yalnız Yiğit'in bilgisiyle durur.

## Hedef düzen

```
VoiceDictation/
├── dictation.py  file_queue.py  README.md  CLAUDE.md  LICENSE  requirements.txt  .gitignore  .mcp.json.example
├── docs/        nasil-calisir.md · kurulum.md · TODO.md · CHANGELOG.md · calibration/ · yapi-sadelestirme-2026-09-16/
├── scripts/     setup.bat · setup.sh · start.vbs (yeni, yolunu kendi bulur) · start.bat · start.sh · VoiceDictation.app
├── tests/       test_file_queue.py
├── data/        GİT DIŞI · değerli · yedeklenir      inbox/ · audio/ · transcripts/
├── .local/      GİT DIŞI · makineye özel · üretilir  logs/ · models/ · file-queue/
└── venv/        GİT DIŞI · platforma özel
Repo dışı (belgelenir): ~/.cache/huggingface/hub (Whisper turbo) · OS temp (LIVE.md, geçici WAV) · Startup kısayolu / Login Items .app
```

Silinen: `_bmad/`, `.claude/skills/bmad-*`, `.agents/` (legacy talimat dosyası analiz klasörüne arşivlenir), kök `start.bat`/`start.vbs`, kök `dictation.log` (içeriği aylık loga birleşir — P0), `docs/auto-start.md` (→ `kurulum.md`, P4 siler), `.playwright-mcp/`, `__pycache__/`. Git'ten çıkan (dosya kalır, ignore): `.codex/config.toml`.

## İş paketleri

Sahipler: Herdr pane ajanları (Opus 5 [1m]); koordinatör (Fable, `voicedictation-scope`) denetler, birleştirir, commit'i Yiğit onayıyla yapar. Her ajan **yalnız kendi dosyalarına** dokunur; aynı çalışma ağacı, worktree yok. **Hiçbir ajan commit atmaz.** Daemon şu an **çalışıyor**: `dictation.py` çalıştırılmaz (`py_compile` hariç), `--transcribe` çalıştırılmaz, Drive'a ve `logs/`'a dokunulmaz.

### P1 — Kod (`opus-yol`, w0:p4) — yalnız `dictation.py`  → `gorev-p1-kod.md`
### P2 — Repo hijyeni (`opus-yapi`, w0:p5) — git ağacı, `.gitignore`  → `gorev-p2-hijyen.md`
### P3 — Kurulum ve başlatma (`opus-ortam`, w0:p6) — `requirements.txt`, `scripts/`  → `gorev-p3-kurulum.md`
### P4 — Belgeler (`opus-techwriter`/Paige, w0:p3) — `README.md`, `CLAUDE.md`, `docs/*.md`  → `gorev-p4-belgeler.md`
### P0 — Veri, log, sistem (koordinatör + Yiğit)
**A. Daemon çalışırken:** P1–P4 düzenlemeleri.
**B. Daemon durdurulur (Yiğit: tray → Çıkış; ~30 dk; rclone 03:00/15:00 dışında):**
1. Log birleştirme: `logs/dictation.log.YYYY-MM-DD` (157) + kök `dictation.log` (Mart) → `.local/logs/YYYY-MM-<Ay>.log`; içerik silinmez; satır sayısı doğrulanınca kaynaklar kaldırılır. Betik scratchpad'den, commit edilmez.
2. Veri kopyası: `robocopy` ile `Records\VoiceDictation\*.md → data\transcripts\`, `Records\RawRecords\* → data\audio\` (**kopya**). Doğrulama: 16 MD / 11 ses (1003,6 MB), sayı + boyut + `Get-FileHash`.
3. Smoke test: `py_compile`; kısa dosyayla `--transcribe` → `data/transcripts/`, `data/audio/`, Kaynak göreli, Drive'da yeni klasör yok; `cscript //nologo scripts\start.vbs` → tray; dikte + 1 dk lecture (Yiğit); `.local/logs/2026-09-Eylül.log`.
4. **Yiğit onayıyla:** Drive `Records/` tamamen silinir (K5). Startup'taki `start.vbs` kopyası → `VoiceDictation.lnk`.
**C.** rclone bir sonraki turda `data/` (~1 GB) yedeğe gider — beklenen.

## Commit sırası (her biri Yiğit onayıyla, koordinatör atar)
1. `feat: file_queue modülü ve testleri` (K3)
2. `chore: BMAD ve eski ajan dosyaları kaldırıldı, .gitignore yeniden yazıldı` (P2)
3. `feat: kurulum ve tek başlatıcı — requirements PEP 508, scripts/start.vbs, setup` (P3)
4. `refactor: veri ve log yolları repo içine — data/, .local/, aylık log, Kaynak göreli` (P1)
5. `docs: belge seti yeniden — README yerel dosyalar tablosu, CLAUDE.md ≤80 satır, nasil-calisir, kurulum, TODO, CHANGELOG` (P4 + analiz klasörü)

## Kapsam dışı / ayrı onay
- `_yedek-config/rclone/filter-yazilim.txt`'ye `- /VoiceDictation/.local/` — ayrı adım.
- HF önbelleğinde `medium` + `small` silme — ayrı onay; `large-v3` iFonzo'da doğrulanmadan dokunulmaz.
- Sonar belgelerindeki `Records\RawRecords` referansları — Sonar oturumunun işi; CHANGELOG'da not.
- Mac tarafı: `.app` yeniden derleme (`path to me`), Login Items, 4 izin, Mac doğrulama listesi — Mac'teki ilk oturum (TODO).

## Doğrulama (uçtan uca)
1. `py_compile` temiz; `grep` ile Drive/Meet/RawRecords referansı sıfır (kod + belgeler, CHANGELOG hariç).
2. `--transcribe` smoke: çıktı `data/transcripts`, ses `data/audio`, Kaynak göreli, aynı adla ikinci çalıştırma zaman eki alır.
3. Daemon `scripts/start.vbs` ile başka cwd'den başlar; dikte + lecture çalışır; Drive'da klasör oluşmaz; log aylık dosyaya yazar.
4. `git status` uygulama kullanımından sonra temiz; `git ls-files` ≈ 30 dosya.
5. `pip install -r requirements.txt --dry-run` Windows'ta çözülür.
6. Belge devir testi: yeni bir ajan yalnız README + CLAUDE.md okuyarak "veri nerede, ne yeniden üretilir, Mac'e ne kopyalanır" sorularına cevap verebiliyor.
