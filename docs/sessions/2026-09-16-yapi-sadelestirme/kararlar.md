# Kararlar — Yiğit, 16 Eylül 2026

Analiz turunun (`derleme.md` §4) açık sorularına Yiğit'in verdiği kararlar. Plan bunların üstüne kurulur.

| # | Karar |
|---|---|
| **K1** | Veri klasörleri **İngilizce**: `data/inbox/`, `data/audio/`, `data/transcripts/`. |
| **K2** | **BMAD çıkar**: `_bmad/`, `.claude/skills/bmad-*`, `.agents/skills/` aynası, `CLAUDE.md` §2. Proje güncel düzene geçer (global `yk-*` skill'ler, iFonzo tarzı belge düzeni). |
| **K3** | `file_queue.py` + `tests/` **commit edilir, iş kapanır.** Koordinatör yorumu: modül + test olarak commit; daemon'a bağlama bu turda yok (kullanım değişmez). **Genel ilke:** programı kullanmak git durumunu kirletmemeli → tüm çalışma çıktıları (`data/`, `.local/`, log, pid, `__pycache__`, üretilen ayar dosyaları) ignore edilir. |
| **K4** | Diarize kodu **kalır** (uyuyan, tray'den çağrılmaz); `TODO.md` "Gelecek" bölümünde yaşar. `models/` → `.local/models/`; venv'e dokunulmaz. |
| **K5** | Drive `Records/` **tamamen** repoya gelir: 11 ses dosyası (Sonar'ın 2 mp4'ü dahil — onlar da VoiceDictation ile dikte edildi) + 16 MD. Doğrulama sonrası Drive'daki `Records/` klasörü (`index.md` dahil) kaldırılır. Sonar belgelerindeki `Records/RawRecords` referansları Sonar projesinde ayrıca güncellenir (not düşülür). |
| **K6** | Cihazlar arası veri eşitlemesi **yok**; sorun değil. Neyin nerede olduğu belgelerde açık yazılır; `Yazilim` yedeği yeterli. Ajan devraldığında belgeden okuyup anlamalı. |
| **K7** | Loglar **tam metinle** kalır (değişmez). Düzen: **aylık dosyalar** ("Temmuz 2026" gibi adlandırma); mevcut 157 günlük dosya aylara birleştirilir. |
| **K8** | `data/inbox/` **elle yönetilen** klasör; işlenen dosyaya ne olacağı Yiğit'e kalır. Mevcut davranışlar korunur: Meet akışı orijinali yerinde bırakır, "dök" akışı bugünkü gibi çalışır. |
| **K9** | Yeni MD'lerde "Kaynak" satırı **repo-göreli**; Drive artık projenin parçası değil. Eski MD'lere dokunulmaz. |

Önerilen varsayılanlar (`derleme.md` §4) itirazsız kabul: `scripts/` adı kalır, loglar `.local/logs/`, tek env `VOICEDICTATION_DATA_DIR`, `requirements.txt` PEP 508 ile tamamlanır, tek `scripts/start.vbs` + Startup kısayolu, `main.scpt` `path to me`, `.codex/config.toml` git'ten çıkar, `.gitignore` yeniden yazılır, belge seti TechWriter önerisi, CHANGELOG tek dosya, aynı ada üstüne yazma düzeltilir, yedek filtresine `.local/` eklenir (ayrı onay), HF'de `medium`+`small` silinebilir (`large-v3` iFonzo'da doğrulanmadan silinmez).
