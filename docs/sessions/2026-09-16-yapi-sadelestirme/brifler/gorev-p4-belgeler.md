# P4 — Belgeler (`opus-techwriter` / Paige)

Önce `plan.md` ve `kararlar.md`'yi oku (aynı klasör). Senin `sonuc-techwriter.md` önerin **onaylandı**; belge seti ve tek görev cümleleri oradaki gibi. `derleme.md` diğer ajanların bulgularını içeriyor (kod gerçekleri için kullan). Tech-writer kimliğinle devam et. **Dosyaların:** `README.md`, `CLAUDE.md`, `docs/nasil-calisir.md`, `docs/kurulum.md`, `docs/TODO.md`, `docs/CHANGELOG.md`, `docs/auto-start.md` (silinecek). Başka dosyaya dokunma. Commit yok. Daemon çalışıyor; programı çalıştırma.

## Sıralama (diğer ajanlar paralel çalışıyor)

1. **Hemen:** `README.md`, `CLAUDE.md`, `docs/nasil-calisir.md`, `docs/kurulum.md` (yeni dosyalar/yeniden yazım).
2. **P2 taşıyınca:** `docs/TODO.md` ve `docs/CHANGELOG.md` (P2 ajanı `git mv` ile `docs/` altına taşıyor; dosya `docs/` altında görünene kadar bekle, kökteki kopyaya dokunma). P2 ayrıca `.agents/legacy-instructions/2026-09-14-agents.md`'yi `docs/yapi-sadelestirme-2026-09-16/eski-agents-2026-09-14.md` olarak arşivliyor — CHANGELOG özü oradan.
3. **P3 not dosyası gelince:** `docs/yapi-sadelestirme-2026-09-16/p3-kurulum-notlari.md` (Mac `.app` `path to me` derleme adımları, Startup kısayolu, requirements açıklaması, MacBook taşıma listesi) → `docs/kurulum.md`'ye işle. Gelmeden önce iskeleti kur, yer tutucu bırakma; gelince tamamla.
4. `docs/kurulum.md` tamamlanınca `git rm docs/auto-start.md`.

## Kodla birebir olması gereken gerçekler (P1 uyguluyor; belgede bunları kullan)

- Klasörler: `data/inbox/` (elle bırakılan ses/video; işlendikten sonra dosyaya program dokunmaz — Meet akışı; "dök" akışı dosyayı `data/audio/`'ya taşır, bugünkü gibi), `data/audio/` (lecture WAV + taşınan sesler), `data/transcripts/` (MD), `.local/logs/` (aylık `YYYY-MM-<Ay>.log`, örn. `2026-09-Eylul.log`, tam metin, silinmez; `dictation.pid`), `.local/models/` (speechbrain, uyuyan diarize), `.local/file-queue/` (`file_queue.py`, daemon'a bağlı değil), `venv/`.
- Env: `VOICEDICTATION_DATA_DIR` (veri kökü, isteğe bağlı), `VOICEDICTATION_EDITOR`; `.env` kökte, git dışı, isteğe bağlı.
- Repo dışı: Whisper turbo `~/.cache/huggingface/hub/` (paylaşımlı önbellek, başka projelerin modelleri de var — silinmez; Mac'te `mlx-community/whisper-turbo`), LIVE.md ve geçici WAV OS temp (`voicedictation_live/`), Windows Startup kısayolu `VoiceDictation.lnk` → `scripts/start.vbs`, Mac Login Items → `scripts/VoiceDictation.app`.
- "Kaynak" satırı yeni MD'lerde repo-göreli (`data/audio/<isim>.wav`); eski MD'lere dokunulmadı.
- Tray menüsü: koddan oku (`dictation.py:636-673`, iki alt menü). Dosya seçiciler `data/inbox/`'ta açılır. `--transcribe FILE`, `--aggressive` CLI aynen.
- Başlatma: Windows `scripts/start.vbs` (yolunu kendi bulur) + Startup kısayolu (`setup.bat` kurar); `scripts/start.bat` konsollu hata ayıklama; Mac `.app` (`path to me`).
- Kurulum: `scripts/setup.bat|sh` → venv + `pip install -r requirements.txt` (PEP 508 platform koşulları); Python 3.14.2 ile test edildi.
- Mac doğrulama borcu (26 Nisan) ve `.app` yeniden derleme → `docs/TODO.md` (tek kopya). `CLAUDE.md` §0.5 hatırlatması tek satır + TODO linki.
- **Gelecek** (`TODO.md`): diarize opt-in (K4, kod uyuyor), `file_queue` daemon bağlantısı, `--calibrate` akışı (`docs/calibration/README.md` anlatıyor, yazılmadı), `.local/` yedek filtresi, Sonar belgelerindeki eski yol.
- CHANGELOG girişi (16 Eylül 2026): kararlar özeti (K1–K9), taşınan/silinen, Drive `Records/` kaldırıldı, **Sonar notu:** `2026-05-01_Sonar-*.mp4` yeni yeri `VoiceDictation/data/audio/`; Sonar belgeleri ayrıca güncellenecek. Eski AGENTS dosyasının özü 1–2 satır.
- Repo public: belgelerde mutlak kişisel yol yok (`~`, göreli); Yiğit'in kullanıcı adı geçmez.

## Kabul

- `grep -rn "Drive'ım\|Meet Recordings\|RawRecords\|VoiceDictation_Lectures\|auto-start.md\|_bmad\|BMAD" README.md CLAUDE.md docs/nasil-calisir.md docs/kurulum.md docs/TODO.md` boş (CHANGELOG tarihçe olarak hariç).
- `CLAUDE.md` ≤ 80 satır. Belgedeki her yol/klasör adı yukarıdaki listeyle birebir.
- Devir testi: yalnız README + CLAUDE.md okuyan biri "veri nerede, ne yeniden üretilir, Mac'e ne kopyalanır, daemon nasıl başlar" sorularına cevap verebilmeli.

## Geri çağrı (tek sefer)

`SendMessage` → `to: voicedictation-67`, mesaj: `hazir: P4 — <3 satır: yazılan belgeler / grep+satır sayısı / açık nokta>`. Hata verirse yalnız `herdr agent get voicedictation-scope` `idle`/`done` iken `herdr agent prompt voicedictation-scope '<aynı mesaj>'`. Sonra pane'de bekle.
