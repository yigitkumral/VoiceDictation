# Görev — opus-yol (koddaki yollar ve veri geçişi)

Önce aynı klasördeki `ortak-brif.md` dosyasını oku; kararlar ve kurallar orada. Sonuç dosyan: `sonuc-yol.md`.

## Odak: kod hangi yerlere dokunuyor, repo içine nasıl gelir

- **Yol envanteri (tablo):** `dictation.py` ve `file_queue.py` içindeki tüm dosya-sistemi yolları ve env değişkenleri: sabit/fonksiyon, satır, amaç, okuma mı yazma mı, Windows/Mac farkı. (`grep -n` ile: `os.path.join`, `expanduser`, `gettempdir`, `DRIVE_`, `FALLBACK_`, `_LOG_DIR`, `savedir`, `os.environ`, `shutil.move`, `open(`.) Ölü/eski yolları ayrıca işaretle: `_get_lectures_dir` shim (`:1096`), eski diarize `_meet.md` yolu (`:2923`, `:2934`), `.env`.
- **Tek yol katmanı önerisi:** Drive → repo içine geçişte yollar **nasıl basit kalır**? Tek bir `PATHS`/ayar bölümü mü, küçük bir `paths.py` mi, ya da hiçbiri (sabitleri repo-göreli yap)? Env override gerekli mi (hangileri: veri kökü, model önbelleği, kuyruk)? Drive fallback (`_ensure_writable_dir`, `:1071`) veri repo içine gelince tamamen kalkar mı? Mac parity için ne gerekir (`~` genişletme, `afconvert`, `.app`)? Önerini **kullanım değişmeden** ve **en az kod değişikliğiyle** kur; büyük refactor önerme.
- **Meet girdi klasörü:** Yiğit Meet kayıtlarını repo içindeki bir klasöre elle bırakacak. Mevcut `_pick_file_and_meet_dictate_plain` (`:2123`+) dosya seçiciyle çalışıyor; seçicinin varsayılan açılış dizini bu klasör olabilir mi — kullanım değişmeden? `--transcribe` / "Ses dosyasını dök" akışındaki `shutil.move` (dış dosyayı `RawRecords`'a taşıma, `:1612`+) veri repo içine gelince ne anlama gelir; Meet akışının "orijinale dokunmaz" kuralı korunur mu?
- **Veri geçişi:** mevcut Drive verisi (16 md + ~1 GB ses; MD'lerde "Kaynak" alanı Drive yolunu gösteriyor) repo içine nasıl taşınır; MD içindeki eski yollar ne olur (dokunulmaz mı, tek seferlik düzeltme mi)? `Records/index.md` ne olur? Adım listesi (analiz düzeyinde, uygulama yok).
- **Kuyruk:** `file_queue.py` `.local/file-queue` — dictation.py'ye bağlı değil; hedef yapıda yeri var mı, yoksa Yiğit'e soru.

## Geri çağrı (bitince, tek sefer)

1. `ListAgents` aracıyla `voicedictation-67 [231d1e]` oturumunun listede olduğunu gör.
2. `SendMessage` ile `to: voicedictation-67`, mesaj: `hazir: C:\Users\yigit\Desktop\Yazilim\VoiceDictation\docs\yapi-sadelestirme-2026-09-16\sonuc-yol.md`
3. Gönderim hata verirse yalnız şu koşulda yedek yol: `herdr agent get voicedictation-scope` çıktısında `agent_status` `idle` veya `done` ise `herdr agent prompt voicedictation-scope 'hazir: <yol>'`. `working`/`blocked` ise gönderme, pane'de bekle.

Sonra oturumu kapatma.
