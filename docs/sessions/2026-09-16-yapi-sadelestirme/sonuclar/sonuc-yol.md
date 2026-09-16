# Sonuç — opus-yol (koddaki yollar ve veri geçişi)

## Bulgular

**Yol envanteri** — satırlar `dictation.py`'den, `fq:` = `file_queue.py`; O = okuma, Y = yazma.

| Yer | Satır | Amaç | O/Y | Not |
|---|---|---|---|---|
| `_LOG_DIR`/`_LOG_FILE` | 47–49, 130 | günlük log, `backupCount=0` | Y | repo-göreli; 157 dosya / 17,6 MB, hiç silinmiyor |
| `_PID_FILE` | 50, 62–93 | daemon kilidi | O/Y | `logs/dictation.pid` |
| `.env` | 96–116 | KEY=VALUE → `os.environ` | O | dosya yok; tek tüketici `_get_hf_token` (119) hiç çağrılmıyor |
| CUDA DLL | 148–156 | `venv/Lib/site-packages/nvidia/*/bin` → PATH | O | yalnız Windows |
| `DRIVE_*` | 222–224 | MD ve ses hedefi | Y | Windows'a özgü `G:\` |
| `FALLBACK_*` + `_ensure_writable_dir` | 225–227, 1071–1082 | Drive yoksa `~/Desktop/VoiceDictation/…` | Y | — |
| `_get_voicedictation_dir`/`_get_rawrecords_dir` | 1085–1092 | tüm çıktıların tek girişi | Y | çağrılar: 1613, 1633, 1928, 1944, 2206, 2235 |
| Whisper modeli | 752 (Win), 749/1171 (Mac) | `WhisperModel("turbo")`, `mlx-community/whisper-turbo` | O | HF önbelleği varsayılan `~/.cache/huggingface/hub`; env yok |
| speechbrain | 1330 | `<repo>/models/spkrec-ecapa-voxceleb` | O/Y | yalnız diarize kullanıyor |
| `shutil.move` | 1612–1630 | dış sesi `RawRecords`'a **taşır** | Y | "zaten içinde" denetimi 1614–1617 |
| `VOICEDICTATION_EDITOR` | 1666 | editör seçimi | — | tek env ayarı |
| LIVE.md | 1823–1829, 1958 | `gettempdir()/voicedictation_live`, sonra silinir | Y | Mac'te `$TMPDIR` (docstring "/tmp" diyor) |
| geçici WAV | 338, 1118 | Mac `afplay` / `afconvert` | Y | yalnız Mac, silinir |
| kuyruk | fq:31–32 | `<base>/.local/file-queue` ya da `VOICEDICTATION_QUEUE_DIR` | O/Y | `dictation.py` içe aktarmıyor (grep boş) |

- **Ölü/eski kod:** `_get_desktop_path` (1066, çağıran yok); `_get_lectures_dir` (1095, tek çağıranı ölü diarize kodu, 2934); diarize `_meet.md` kaynağın yanına (2923) ve kopyası (2934–2935) — `_pick_file_and_meet_dictate` (2764) hiçbir yerden çağrılmıyor (tray 565/627 plain sürümü çağırıyor); `_get_hf_token`; kökteki Mart tarihli `dictation.log`; `.gitignore:11-12,20,28` satırlarının karşılığı yok.
- **Mac hatası (Python ile benzetildi, diske yazılmadı):** `posixpath.join(r"G:\Drive'ım\Records","VoiceDictation")` göreli yol veriyor. Mac'te çıktılar çalışma klasöründe, yani repo içinde, `G:\Drive'ım\Records/` adlı bir klasöre yazılır. Fallback hiç devreye girmez. Hedef yapıda bu hata kendiliğinden ortadan kalkar.
- **Sabit yollar:** Startup klasöründeki `start.vbs` kopyası ve `.app/…/main.scpt` (`/Users/yigitkumral/Desktop/Yazılım/VoiceDictation`, `ı` harfiyle).
- **Aynı ada yazma:** lecture WAV/MD (1928, 1944) ve "dök" akışının MD'si (1634) aynı adlı dosyanın üstüne yazıyor. Yalnız Meet akışı (2208, 2237) ve "dök" akışının sesi (1620) ada zaman eki ekliyor.
- **Drive'daki `Records/RawRecords` klasörünü Sonar da kullanıyor:** Sonar'ın `CLAUDE.md:48,66`, `README.md:46`, `docs/README.md:43`, `docs/toplanti-kayitlari/README.md:37` belgeleri buradaki 2 mp4'ü tek kaynak sayıyor. `kayit-notu` skill'i ise (`references/dagitim-migration-kontrol.md:20`, `.agents` aynası dahil) bu klasöre **yazıyor**.
- **HF önbelleğini başka projeler de kullanıyor:** Qwen3-Embedding (7,5 GB), gliner ve bert-turkish-ner aynı yerde. iFonzo `README.md:63`'te VoiceDictation'dan bağımsız bir large-v3 ses aracı var, yani Systran large-v3 büyük olasılıkla onun. `HF_HOME` taşınmamalı.
- **Drive'daki 16 MD'nin "Kaynak" satırları** (içerik okunmadı, yalnız türe göre sayıldı): 3'ünde mutlak `G:\Drive'ım\…` yolu, 2'sinde parantezli not, 6'sında başka biçim var; 5'inde bu satır yok.

## Öneri

**Tek yol bölümü, `dictation.py` içinde olsun.** Ayrı `paths.py` gerekmez, tek dosya düzeni korunur. 216–227. satırların yerine:
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("VOICEDICTATION_DATA_DIR") or os.path.join(BASE_DIR, "data")
INBOX_DIR = os.path.join(DATA_DIR, "inbox")              # elle bırakılan girdiler
AUDIO_DIR = os.path.join(DATA_DIR, "audio")              # eski Records/RawRecords
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")  # eski Records/VoiceDictation
```
- `_ensure_writable_dir` ile `DRIVE_*`/`FALLBACK_*` **tamamen kaldırılır**. İki getter yalnız `os.makedirs(..., exist_ok=True)` yapıp yolu döndürür. `_LOG_DIR`, `models/` ve CUDA yolu da `BASE_DIR`'i kullanır, böylece tek kök kalır.
- **Yalnız bir env değişkeni:** `VOICEDICTATION_DATA_DIR`, başka disk ya da cihaz gerekirse diye. Model önbelleği için env eklenmez (önbellek başka projelerle ortak), yalnız belgelenir. Ayarlar için tek yer mevcut `.env` yükleyicisidir: cihaza özel, git dışı.
- `.gitignore`'a tek satır eklenir: `data/`. Ölü `_get_desktop_path` ve `_get_lectures_dir` silinir. Diarize kodu kalırsa `_meet.md` kaynağın yanına değil, `TRANSCRIPTS_DIR`'e yazılır.
- **Mac uyumu:** kök `__file__`'dan çıktığı için `~` genişletmeye gerek kalmaz. `afconvert` ve `gettempdir` olduğu gibi kalır. Repo yolu değişirse yalnız `.app` yeniden derlenir (`docs/auto-start.md:73`).
- **Girdi klasörü (kullanım aynı kalır):** iki dosya seçici de `INBOX_DIR`'de açılır. Windows'ta `askopenfilename(initialdir=INBOX_DIR)` (2093, 2149), Mac'te `choose file … default location (POSIX file "…")` (2061). "Dök" akışında `shutil.move`, dosyayı inbox'tan `audio/`'ya taşımış olur; bu da "işlendi" anlamına gelir. Meet akışı "orijinale dokunmaz" kuralını korur: mp4 inbox'ta kalır, WAV `audio/`'ya yazılır. Kodda Meet'in Drive düzenini bilen yerler temizlenir (2125'teki yorum, 2199–2201 ve 2894–2896'daki "(1) suffix" metni).
```
VoiceDictation/
├── dictation.py        # yol bölümü: BASE_DIR / DATA_DIR
├── data/     (git dışı, rclone yedeğine girer)
│   ├── inbox/          # Yiğit'in elle bıraktığı ses/video (Meet dahil)
│   ├── audio/          # lecture WAV'ları + taşınan sesler
│   └── transcripts/    # MD transkriptler
├── logs/     (git dışı) # log + dictation.pid
├── models/   (git dışı) # yalnız diarize (speechbrain)
├── .local/   (git dışı) # yalnız kuyruk kalırsa
└── .env      (git dışı, isteğe bağlı) # VOICEDICTATION_DATA_DIR, VOICEDICTATION_EDITOR
Repo dışı (yerleri belgelenir): HF önbelleği (turbo 1,5 GB) · OS temp (LIVE.md) · venv/ · Startup start.vbs / Login Items .app
```
**Veri geçişi:**
1. Daemon'u durdur; rclone saatlerinin (03:00 / 15:00) dışında çalış.
2. Yol değişikliğini ve `.gitignore` satırını uygula.
3. `robocopy` ile **kopyala** (taşıma değil): `Records\VoiceDictation\*.md` → `data\transcripts\`, `Records\RawRecords\*` → `data\audio\`. Ardından sayı ve boyutu doğrula (16 MD; 11 dosya, 1003,6 MB).
4. Uzantısı olmayan tek dosyanın türünü belirle.
5. Eski MD'lerdeki "Kaynak" satırlarına **dokunma**: tarihsel kayıt; dosya adları değişmediği için dosyalar yine bulunur.
6. Drive'daki kopyaları sil ya da bırak (1. ve 2. soruya bağlı). `Records/index.md`'de VoiceDictation bölümünün yerine "repo içine taşındı (tarih)" notu koy.
7. `CLAUDE.md`, `README.md` ve `TODO.md`'deki Drive satırlarını (yaklaşık 10 yer) güncelle; `CHANGELOG.md` tarihçe olduğu için kalır.

**Kuyruk:** `file_queue.py` koda bağlı değil. Hedeflediği kullanıcı iFonzo WhatsApp hattıydı (`file_queue.py:4`); o hat artık bağımsız bir ses aracı kullanıyor (iFonzo `README.md:63`). Önerim: hedef yapıya alınmasın. Bağlanacaksa mevcut `.local/file-queue` yeri yeterli.

## Riskler / Açık sorular

1. Drive, transkriptlere Windows ve Mac'ten ortak erişim sağlıyordu. `data/` git dışında olduğu için her cihazda ayrı kalır; Mac'te üretilen dosyalar Windows'a gelmez. Bu kabul edilebilir mi?
2. Sonar, Drive'daki `RawRecords` klasörünü hem okuyor hem yazıyor. `Records/` Sonar için kalacak mı? 2 Sonar mp4'ü `data/audio/`'ya taşınırsa Sonar'da 4 belge ve 3 skill dosyası (ayna dahil 6) güncellenmeli.
3. Brife göre rclone `data/` klasörünü (~1 GB) zaten Drive'a yedekliyor. Drive'daki eski `Records/` kopyaları silinsin mi (aynı veri iki kez tutulmasın)?
4. Yeni MD'lerde "Kaynak" yolu repo-göreli yazılsın mı (`os.path.relpath`)? Böylece Mac'te de anlamlı olur, ama çıktı biçiminde küçük bir değişiklik demek.
5. Meet mp4'leri inbox'ta birikecek. Elle mi temizlenecek, yoksa "dök" akışındaki gibi `audio/`'ya mı taşınsın (bu bir davranış değişikliği)?
6. Aynı adlı dosyanın üstüne yazma sorunu (lecture WAV/MD, "dök" MD'si) tek bir yardımcı fonksiyonla düzeltilsin mi? Tüm veri tek yerde toplanınca bu risk artıyor.
7. `file_queue.py`, `tests/` ve `.gitignore`'daki `.local/` satırı ne olacak: koda bağlanacak mı, silinecek mi? Diarize kodu ile `models/` (85 MB; HF önbelleğinde ikinci kopyası da var) kalacak mı?
8. Klasör adları `data/{inbox,audio,transcripts}` mı olsun, Türkçe `kayitlar/{gelen,ses,transkript}` mi? Repo kökünde bugün hep İngilizce adlar var.
