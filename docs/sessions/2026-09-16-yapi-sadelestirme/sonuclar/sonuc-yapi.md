# Sonuç — opus-yapi (repo ağacı ve hijyen) · 16 Eylül 2026

## Bulgular

**Hacim:** Git'te 1534 dosya var; bunun **1509'u (%98) BMAD**: `_bmad/` 1147 dosya ve `.claude/skills/` 362 dosya. Uygulamanın kendisi `dictation.py` ile 25 dosyadır. Diskteki en büyük parçalar git dışında kalıyor: `venv/` (31 786 dosya, 2,9 GB), `models/` (85 MB), `logs/` (157 dosya, 19 MB). Görsel gürültü yapanlar `_bmad/`, `.agents/`, `.playwright-mcp/`, kökteki `dictation.log`, `start.*`, `__pycache__/` ve `calibration/`.

**Kök öğe kararları:**

| Öğe | Karar | Gerekçe |
|---|---|---|
| `dictation.py`, `README.md`, `CLAUDE.md`, `LICENSE` | kalsın | Başlatma, CLI ve `VoiceDictation.app` kökteki `dictation.py` yoluna bağlı |
| `requirements.txt` | kalsın, tamamlansın | Dosyada 5 paket var. `pystray`+`Pillow` (Win) ve `rumps` (Mac) eksik. `dictation.py:450`, `:579` bunları korumasız import ediyor, `:3660` çağrısında yedek yol yok. Bu yüzden `setup.*` ile sıfırdan kurulan MacBook'ta tepsi/menü açılışta çöker. Mevcut `venv` elle tamamlanmış |
| `CHANGELOG.md`, `TODO.md` | taşınsın → `docs/` | iFonzo düzeni: kökte yalnız README/CLAUDE kalır |
| `calibration/` (2 dosya) | taşınsın → `docs/calibration/` | Kod bu klasöre başvurmuyor; içeriği belge ve referans metin |
| `docs/auto-start.md` | kalsın, düzeltilsin | `:9`, `:12-13` "start.vbs, start.bat'i çalıştırır" diyor; `start.vbs` ise doğrudan `pythonw` çalıştırıyor (CLAUDE.md:207 de aynı hatayı taşıyor). README:221-226 ile konu iki yerde yazılı |
| `scripts/` | kalsın | Kökteki başlatıcılar buraya toplansın. README:54-55 `./setup.sh` yazıyor; dosya `scripts/` altında |
| kök `start.bat`, `start.vbs` (ignore'lu) | silinsin → yerine tek `scripts/start.vbs` | İçlerine mutlak yol gömülü. Startup'taki dosya kısayol değil, birebir **kopya** (README "kısayol koy" diyor). Şu an 3 başlatma yolu var: kök bat (`pythonw`), `scripts/start.bat` (konsollu), vbs. Yeni vbs yolu kendi konumundan bulmalı |
| kök `dictation.log` (682 KB) | silinsin | Son yazım 17 Mart; log aynı gün `logs/` klasörüne taşındı (`bdb7d14`) |
| `logs/` | taşınsın → `.local/logs/` | `backupCount=0` ile hiç silinmiyor (`dictation.py:132`). PID dosyası da burada (`:50`) |
| `models/` (speechbrain) | taşınsın → `.local/models/` ya da silinsin | Yalnız tray'den çağrılmayan diarize yolu kullanıyor (`:1330`). Aynı model HF cache'te de var |
| `venv/` | kalsın (kökte, ignore'lu) | Python alışkanlığı; `setup.*`, `start.*` ve `.app` buna bağlı |
| `file_queue.py`, `tests/`, `.gitignore`'daki `+.local/` | **yarım iş** | 15 Eyl 21:13–21:14'te birlikte yazılmışlar, commit edilmemişler. `dictation.py` import etmiyor, hiçbir belge anmıyor. Docstring'e göre amaç iFonzo WhatsApp hattının daemon'a dosya kuyruğu bırakması → S2 |
| `_bmad/`, `.claude/skills/` (116 `bmad-*`) | Yiğit karar verecek → S1 | Kullanım izi yok (aşağıda) |
| `.agents/skills/` (untracked) | BMAD kararına bağlı | `sync-claude.py` aynası; `diff -rq` ile `.claude/skills` arasında fark yok |
| `.agents/legacy-instructions/` | özü changelog'a aktarılıp silinsin | 16 KB'lik eski `AGENTS.md`; yalnız yerel `.git/info/exclude:7` ile gizleniyor |
| `.codex/config.toml` (git'te) | git'ten çıkarılıp ignore edilsin | İçinde `C:\Python314` ve iFonzo mutlak yolları var, Mac'te çalışmaz. iFonzo'da bu dosya ignore'lu ve üretilir (`iFonzo/docs/README.md`) |
| `.mcp.json` (ignore'lu), `.mcp.json.example` | kalsın | iFonzo ile aynı desen; iki dosyada da aynı 4 sunucu var |
| `.claude/settings.local.json` | kalsın (ignore'lu) | Makineye özel |
| `.playwright-mcp/` (4 log, 19 Mart) | silinsin, ignore'da kalsın | Eski konsol çıktısı |
| `__pycache__/`, `tests/__pycache__/` | silinsin | cpython-314 çöpü |
| `docs/yapi-sadelestirme-2026-09-16/` | kalsın | Global desen: `docs/<konu>-<tarih>/` |

**`.gitignore` sorunları:**
- Genel `settings.json` kuralı `.claude/settings.json` dosyasını da yutuyor (`git check-ignore` ile doğrulandı).
- `.dictation.log`, `.dictation.pid` ve `pretrained_models/` ölü kurallar.
- `logs/`, `models/`, `start.*` kuralları hedef yapıda gereksiz kalıyor.

**BMAD izi:**
- Kurulum v6.1.0, 14 Mart 2026; o günden beri güncellenmemiş (`_bmad/_config/manifest.yaml`).
- Çıktı klasörü `_bmad-output` yok; PRD, story veya sprint dosyası da yok.
- 33 commit'ten yalnız kurulum commit'i (`09928fb`) BMAD'e dokunuyor.
- Global skill'lerde `bmad-*` yok; yerlerini `yk-brainstorm`, `yk-elicit`, `yk-party` almış.
- CLAUDE.md §2, BMAD'i "kullanılan yöntem" olarak anlatıyor.
- BMAD, IhalePilot, UYAPEsatis ve Zugzwang'da da kurulu.

## Öneri

```
VoiceDictation/
├── CLAUDE.md  README.md  LICENSE  requirements.txt  .gitignore  .mcp.json.example
├── dictation.py            # uygulama (tek dosya kalır; kullanım değişmez)
├── docs/                   # README.md (harita) · TODO.md · CHANGELOG.md · auto-start.md · calibration/ · <konu>-<tarih>/
├── scripts/                # setup.bat|sh · start.bat|sh · start.vbs (yolu kendi konumundan bulur) · VoiceDictation.app
├── tests/                  # (file_queue kalırsa)
├── data/                   # GIT DIŞI — kullanıcı verisi, silinmez, yedeklenir
│   ├── inbox/              # Yiğit'in elle bıraktığı ses/video (Meet kaydı dahil)
│   ├── transcripts/        # <isim>.md   ← Records/VoiceDictation
│   └── audio/              # <isim>.*    ← Records/RawRecords
├── .local/                 # GIT DIŞI — makineye özel, silinip yeniden üretilebilir
│   └── logs/  models/  file-queue/
└── venv/                   # GIT DIŞI — platforma özel, setup betiği kurar
```

- **İki git dışı kök yeterli:** `data/` değerli ve kalıcı veridir; `.local/` atılabilir çalışma dosyalarıdır. Geçici dosyalar sistem temp'inde kalır (brif kararı 4). Klasörlerin ne olduğu tek yerde, `docs/README.md` tablosunda anlatılır.
- **Adlandırma kuralı:** klasör adı tek kelime, İngilizce, küçük harf (gerekirse `-`). Belge dosya adları BÜYÜK harf (`README`/`CLAUDE`/`TODO`/`CHANGELOG`). Belge içerikleri Türkçe.
- **Hedef `.gitignore`:**
  `venv/` · `__pycache__/` · `*.py[co]` · `.local/` · `data/` · `.env` · `.mcp.json` · `.codex/config.toml` · `.claude/settings.local.json` · `.playwright-mcp/` · `.DS_Store` · `Thumbs.db` · `.vscode/` · `.idea/`
  BMAD kalırsa buna `_bmad-output/` eklenir.

## Riskler / Açık sorular

- **S1 — BMAD:** BMAD bu projede hiç kullanılmamış görünüyor ve takip edilen dosyaların %98'ini oluşturuyor. Kaldıralım mı (`_bmad/`, `.claude/skills/bmad-*`, `.agents/skills/`, CLAUDE.md §2), yoksa diğer projelerle tutarlılık için kalsın mı?
- **S2 — `file_queue.py`:** Commit edilmemiş dosya kuyruğu işi (iFonzo WhatsApp → daemon) bu sadeleştirmeden önce tamamlanıp bağlansın mı, yoksa ayrı branch'e alınıp kökten çıksın mı?
- **S3 — `data/inbox`:** İşlenen dosya `audio/` klasörüne taşınsın mı (tek ses arşivi, `--transcribe` gibi), yoksa yerinde kalsın mı (bugünkü Meet akışı gibi; o durumda inbox şişer)?
- **S4 — Yedek:** rclone filtresi yalnız `venv/` klasörünü dışarıda bırakıyor. `data/` (~1 GB ve büyüyor) Drive'a yedeklenmeye devam etsin mi? `.local/` (model ve log) filtreye eklenip hariç tutulsun mu? Bu değişiklik `_yedek-config` tarafında yapılır.
- **S5 — Loglar:** Loglar sınırsız tutulsun mu, yoksa ör. 60 günlük rotate sınırı konsun mu?
- **S6 — speechbrain:** Diarize ileride geri açılacak mı? Açılmayacaksa `models/` ve torch/sklearn bağımlılıkları kaldırılabilir; açılacaksa HF cache'teki kopya yeterli mi?
- **Risk:** Startup'taki `start.vbs` kopyası ve `VoiceDictation.app` mutlak yol taşıyor; `main.scpt` içinde `cd '/Users/yigitkumral/Desktop/Ya…/VoiceDictation'` gömülü. Yeni Mac'te kullanıcı adı ya da klasör değişirse `.app` yeniden derlenmeli. Windows'ta da Startup kopyası yenilenmeli.
