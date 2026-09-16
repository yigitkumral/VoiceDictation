# Ortak brif — VoiceDictation yapı sadeleştirme analizi (16 Eylül 2026)

Koordinatör: Claude Fable 5.1 — Herdr ajanı `voicedictation-scope` (pane `w0:p1`), Claude oturum adı `voicedictation-67 [231d1e]`.
Karar sahibi: Yiğit. Bu tur **yalnız analiz**; uygulama, Yiğit ile tartışıldıktan sonra ayrı planlanacak.

## Durum ve amaç

- Proje: `C:\Users\yigit\Desktop\Yazilim\VoiceDictation` — tek dosya `dictation.py` (3670 satır) + çevresi. Aylar sonra ilk büyük bakım turu.
- Yiğit'in şikâyeti: dosya yapısı karmaşıklaştı, artık onun genel zihniyetini yansıtmıyor.
- Referans zihniyet: **iFonzo** projesinin üst düzey düzeni — `C:\Users\yigit\Desktop\Yazilim\iFonzo` kökünde yalnız `CLAUDE.md`, `README.md`, `docs/`, `tools/`; `docs/` altında `README.md`, `TODO.md`, `arsiv/`, `changelog/`, `sessions/`… Basit, az parça, her şeyin tek belli yeri var. iFonzo'nun iç detayları ilgilendirmez; **klasör düzeni ve işleyiş** (belge nerede, araç nerede, iş nasıl takip ediliyor) önemli.

## Yiğit'in verdiği kararlar (sorgulanmaz, üstüne inşa edilir)

1. Drive'daki `G:\Drive'ım\Records\{VoiceDictation,RawRecords}` düzeni **repo içine alınacak**: transkript MD'leri ve ses dosyaları proje ağacında yaşayacak (git dışı).
2. Proje yerel dosyalara ihtiyaç duyar (venv, model önbelleği, log, veri, geçici) — sorun değil; ama **nerede, neden, nasıl** olduğu proje yapısında açıkça belgelenmeli. Başka bir ajan başka bir cihazda (proje **MacBook'a taşınacak**) devraldığında neyin ne olduğunu bilmeli.
3. **Meet kayıtları projeden tamamen çıkıyor.** Kod ve belgeler Drive'daki Meet klasörünü bilmeyecek, adını anmayacak. Yalnız repo içinde Yiğit'in **elle dosya bıraktığı bir girdi klasörü** olacak (adı öneri konusu). Meet kayıtlarını oraya getirmek Yiğit'in işi.
4. Geçici dosyalar (LIVE.md, geçici WAV) önemli değil; yerelde geçici kalabilir.
5. **Kullanım değişmeyecek**: hotkey, tray menüsü, "Diktasyon" wake word, `--transcribe` CLI, çıktıların içeriği aynı kalır. Bu bir sadeleştirme, yeni özellik değil.
6. **Aşırı karmaşıklaştırma yok**: öneriler basit, az parça, az kural. Tercih: tek konfigürasyon noktası, düz klasör adları, tek yerde belge.

## Bilinen envanter (koordinatör salt-okuma çıkardı — doğrula, körü körüne güvenme)

- **Repo kökü:** `.agents/` (untracked; BMAD skill aynası + `legacy-instructions/`), `.claude/`, `.codex/`, `.playwright-mcp/`, `_bmad/` (1147 dosya), `calibration/` (2 dosya), `docs/auto-start.md`, `logs/` (157 dosya, 17,5 MB; günlük rotate, hiç silinmiyor), `models/spkrec-ecapa-voxceleb/` (85 MB speechbrain), `scripts/` (`setup.bat/sh`, `start.bat/sh`, `VoiceDictation.app`), `tests/test_file_queue.py` (untracked), `venv/` (2,8 GB), kökte `start.bat` + `start.vbs` (gitignore'da), eski `dictation.log` (680 KB, Mart), `dictation.py`, `file_queue.py` (untracked; `dictation.py` henüz kullanmıyor), `CLAUDE.md` (16 KB), `README.md` (14 KB), `CHANGELOG.md`, `TODO.md`, `LICENSE`, `requirements.txt`, `.mcp.json` + `.mcp.json.example`, `.gitignore` (değişik: `.local/` eklendi).
- **Kodda dış yollar:** `DRIVE_RECORDS_BASE = r"G:\Drive'ım\Records"` (`dictation.py:222`), fallback `~/Desktop/VoiceDictation/` (`:225`), `_LOG_DIR = <repo>/logs` (`:47`), PID `logs/dictation.pid` (`:50`), `.env` repo kökünde (`:98`), speechbrain `savedir=<repo>/models/...` (`:1330`), LIVE `tempfile.gettempdir()/voicedictation_live` (`:1827`), geçici WAV `tempfile.NamedTemporaryFile` (`:338`, `:1118`), `VOICEDICTATION_EDITOR` env (`:1666`), `file_queue.queue_root` → `<repo>/.local/file-queue` veya `VOICEDICTATION_QUEUE_DIR` env. Eski diarize yolu `_meet.md`'yi kaynak sesin yanına yazıyor (`:2923`, `:2934`) — tray'den çağrılmıyor.
- **Whisper modelleri** HF cache'te (`~/.cache/huggingface/hub/`): kullanılan `mobiuslabsgmbh/faster-whisper-large-v3-turbo` (1,5 GB); kodda referansı olmayanlar: Systran large-v3 (2,9 GB, 15 Eylül'de değişmiş), medium (1,4 GB), small (0,45 GB). speechbrain modeli HF cache'te de var (çift kopya). `HF_HOME` tanımsız.
- **Drive:** `Records/VoiceDictation/` 16 md (0,6 MB); `Records/RawRecords/` 11 dosya (~1 GB: mp4×2, qta×4, aac, wav×2, m4a, uzantısız×1); `Records/index.md` ortak dizin notu (birden çok proje için tasarlanmış, aktif tek proje VoiceDictation).
- **Başlangıç:** Windows Startup klasöründe `start.vbs` **kopyası** (repo yolu içine sabit yazılmış); Mac: `scripts/VoiceDictation.app` (Login Items). Görev Zamanlayıcı / Run kaydı yok.
- **Yedek:** `Yazilim` ağacı rclone ile Drive'a günlük 03:00 ve 15:00; filtre (`_yedek-config/rclone/filter-yazilim.txt`) `venv/` hariç; `logs/`, `models/`, `.local/` dahil.
- **Mac doğrulaması:** son 26 Nisan 2026; sonraki paketler yalnız Windows'ta doğrulandı (CLAUDE.md §0.5, TODO.md).

## Kurallar

- **Salt okuma.** Repo, Drive, iFonzo: hiçbir dosyayı değiştirme, taşıma, silme, yeniden adlandırma. Tek yazma hakkın kendi sonuç dosyan.
- **Kullanıcı verisinin içeriğini okuma ve raporlama:** transkript MD içerikleri, ses dosyaları, `logs/` içerikleri yalnız ad/boyut/sayı düzeyinde. iFonzo'da yalnız üst düzey klasör adları + `README.md` + `CLAUDE.md` + `docs/README.md`; `tools/browser/tmp/`, oturum kayıtları, mesaj içerikleri okunmaz.
- Daemon'a dokunma (çalışıyor olabilir), commit/push yok, `pip`/kurulum yok, başka ajan/alt ajan açma, tarayıcı/WhatsApp kullanma.
- `dictation.py` büyük — gerekli bölümleri oku (`grep` ile bul), tümünü yorumlamaya kalkma.
- Diğer ajanların `sonuc-*.md` dosyalarını **okuma** — görüşlerin bağımsız kalsın.

## Çıktı

- Dosya: `docs/yapi-sadelestirme-2026-09-16/sonuc-<ad>.md` (ad görev dosyasında). **En fazla ~1 sayfa**, madde madde, Türkçe.
- Bölümler: **Bulgular** (kanıtlı: `dosya:satır` veya yol) · **Öneri** (hedef klasör ağacı taslağı dahil, kısa ve kararlı) · **Riskler / Açık sorular** (Yiğit'in karar vermesi gerekenler, soru biçiminde).
- Bitince **tek** kısa geri çağrı (yöntem görev dosyasında), "aldım/başlıyorum" zinciri yok. Geri çağrıdan sonra oturumu kapatma; Yiğit sana soru sorabilir.
