# P1 — Kod: yol katmanı ve akışlar (`opus-yol`)

Önce `plan.md` ve `kararlar.md`'yi oku (aynı klasör). Kendi analizin `sonuc-yol.md` temel alındı. **Yalnız `dictation.py`'yi düzenle.** Commit yok. Daemon çalışıyor: `dictation.py`'yi çalıştırma, `--transcribe` çalıştırma; yalnız `venv\Scripts\python -m py_compile dictation.py`. Drive'a, `logs/`'a, `data/`'ya dokunma. Dosyanın mevcut üslubuna uy (ASCII Türkçe yorumlar, mevcut isimlendirme).

## Yapılacaklar

1. **Tek yol bloğu** — `:216-227` (`DRIVE_*`, `FALLBACK_*`) yerine, dosyanın **en başına** (`_LOG_DIR` tanımından önce, `:47` civarı) taşınacak blok:
   ```python
   # --- YOLLAR: her sey repo koku altinda (16 Eylul 2026 duzeni) ---
   BASE_DIR = os.path.dirname(os.path.abspath(__file__))
   DATA_DIR = os.environ.get("VOICEDICTATION_DATA_DIR") or os.path.join(BASE_DIR, "data")   # git disi, degerli
   INBOX_DIR = os.path.join(DATA_DIR, "inbox")              # kullanicinin elle biraktigi ses/video
   AUDIO_DIR = os.path.join(DATA_DIR, "audio")              # lecture WAV + tasinan sesler (eski RawRecords)
   TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")  # MD transkriptler (eski Records/VoiceDictation)
   LOCAL_DIR = os.path.join(BASE_DIR, ".local")             # git disi, makineye ozel, yeniden uretilir
   _LOG_DIR = os.path.join(LOCAL_DIR, "logs")
   MODELS_DIR = os.path.join(LOCAL_DIR, "models")           # speechbrain (diarize, uyuyan)
   ```
   `.env` yükleyici (`:96-116`) kökte kalır; env değişkeni `.env`'den de gelebilsin diye `.env` yükleme **bu bloktan önce** çalışmalı (sıra: `_load_env_file()` → yol bloğu → logging). `_PID_FILE` `_LOG_DIR` altında kalır. Başlangıçta (`main()` girişinde ve `_run_headless_transcribe`'da) `INBOX_DIR`, `AUDIO_DIR`, `TRANSCRIPTS_DIR`, `_LOG_DIR`, `MODELS_DIR` için `os.makedirs(..., exist_ok=True)` — klasör ağacı görünür olsun.
2. **Fallback kalkar:** `_ensure_writable_dir` (`:1071`), `_get_desktop_path` (`:1066`) silinir. Getter'lar yeniden adlandırılır ve sadeleşir: `_get_transcripts_dir()` → `os.makedirs(TRANSCRIPTS_DIR, exist_ok=True); return TRANSCRIPTS_DIR`; `_get_audio_dir()` aynı. Çağrılar güncellenir: `:1613, :1633, :1928, :1944, :2206, :2235`, shim `_get_lectures_dir` (`:1095`, diarize kodu için kalır, yeni getter'a yönlenir), diarize `:2934`. Yazılamayan hedef açık `OSError` verir (yakalayıp Desktop'a düşme yok).
3. **Aynı ada üstüne yazma:** tek yardımcı
   ```python
   def _unique_path(directory, stem, ext):
       """<directory>/<stem><ext>; varsa <stem>_YYYYmmdd_HHMMSS<ext> (ustune yazma yok)."""
   ```
   Kullanım yerleri: `:1619-1622` (dök ses), `:1634` (dök MD — bugün eziyor), `:1928` (lecture WAV — eziyor), `:1944` (lecture MD — eziyor), `:2207-2209` (Meet WAV), `:2236-2238` (Meet MD). Davranış bugünkü Meet akışıyla aynı (zaman eki).
4. **Kaynak satırı göreli (K9):** `_write_lecture_markdown` (`:1282`): `source_path` gerçek bir yol ve `BASE_DIR` altındaysa `os.path.relpath(source_path, BASE_DIR)` (Windows'ta da `/` ayırıcıyla yaz: `.replace(os.sep, "/")`), değilse olduğu gibi; `:1947`'deki yer tutucu metin (`"(WAV diske yazilamadi — ...)"`) bozulmasın (`os.path.isabs` kontrolü yeter).
5. **Dosya seçiciler `INBOX_DIR`'de açılır:** `askopenfilename(initialdir=INBOX_DIR, ...)` (`:2093`, `:2149`); Mac `_pick_audio_file_macos` (`:2060-2064`): `choose file with prompt "..." of type {...} default location (POSIX file "<INBOX_DIR>")` — `INBOX_DIR` önceden `makedirs`.
6. **Drive/Meet bilgisi temizlenir:** yorum bloğu `:2120-2127` ve docstring `:2130-2134` yeni düzeni anlatır ("RawRecords/VoiceDictation/Meet Recordings" sözcükleri geçmez); `:2196-2202` ve `:2894-2896` metinleri genel olur (örn. `"Dosya cok kisa ({audio_dur:.1f}sn); konusma icermiyor olabilir."`); hata metinlerindeki `logs/dictation.log` (`:2189, :2216, :2225, :2248, :2258, :2903, :2952`) → `.local/logs/` (sabit metin ya da `_LOG_DIR`'den türet). Dosya başındaki modül docstring'i/yorumları da yeni düzene göre güncelle.
7. **speechbrain `savedir`** (`:1330-1331`) → `os.path.join(MODELS_DIR, "spkrec-ecapa-voxceleb")`. Diarize kodu (K4) **kalır**, çağrılmaz.
8. **Aylık log (K7):** `TimedRotatingFileHandler` (`:130-135`) yerine:
   ```python
   _AYLAR = ["Ocak","Subat","Mart","Nisan","Mayis","Haziran","Temmuz","Agustos","Eylul","Ekim","Kasim","Aralik"]
   class MonthlyFileHandler(logging.FileHandler):
       """Ay degisince dosyayi kapatip .local/logs/YYYY-MM-<Ay>.log acar; hicbir log silinmez."""
   ```
   Dosya adı: `f"{yil:04d}-{ay:02d}-{_AYLAR[ay-1]}.log"` (örn. `2026-09-Eylul.log`; ASCII ay adı — Türkçe karakterli dosya adı PowerShell/argparse sorunlarından kaçınmak için). Her `emit`'te ay değiştiyse `self.stream` kapatılıp yeni dosya açılır; `encoding="utf-8"`, `delay=False`. `_LOG_FILE` adı artık dinamik: `main()`'deki `print(f"  Log dosyasi  : {_LOG_FILE}")` (`:3595`) `_LOG_DIR`'i basar. Tam metin loglama **değişmez** (K7).
9. `file_queue.py` çağrılmıyor; dokunma. `VOICEDICTATION_EDITOR` (`:1666`) aynen kalır.

## Kabul

- `venv\Scripts\python -m py_compile dictation.py` temiz.
- `grep -n "Drive'ım\|Drive\|RawRecords\|Meet Recordings\|Desktop\|VoiceDictation/\|_ensure_writable_dir\|FALLBACK\|TimedRotating" dictation.py` → yalnız gerekçeli tarihçe yorumu kalabilir; yol/akış olarak **sıfır**.
- Değişen satırların listesi (fonksiyon adı + eski→yeni) kısa bir tablo olarak geri çağrı mesajında.
- Çalışma zamanı testi P0-B'de (daemon kapalıyken) koordinatör yapar; `--transcribe` ile ilk denemede sorun çıkarsa seni yeniden çağırırım.

## Geri çağrı (tek sefer)

`SendMessage` → `to: voicedictation-67`, mesaj: `hazir: P1 — <3 satır: ne değişti / py_compile sonucu / açık nokta>`. Hata verirse yalnız `herdr agent get voicedictation-scope` `idle`/`done` iken `herdr agent prompt voicedictation-scope '<aynı mesaj>'`. Sonra pane'de bekle.
