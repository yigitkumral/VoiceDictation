# Derleme — VoiceDictation yapı sadeleştirme analizi

Koordinatör: Claude Fable 5.1 (`voicedictation-scope`), 16 Eylül 2026. Yalnız derleme; kendi analizim yok.
Kaynaklar (bağımsız çalıştı, birbirini okumadı): `sonuc-astra.md` (Codex gpt-6-astra, reasoning high — `/status` ile doğrulandı), `sonuc-techwriter.md` (Opus 5 [1m], BMAD tech-writer kimliği), `sonuc-yapi.md`, `sonuc-yol.md`, `sonuc-ortam.md` (Opus 5 [1m], xhigh).

## 1. Uzlaşı — beş rapor aynı iskelete yakınsıyor

**Hedef ağaç (ortak payda):**
```
VoiceDictation/
├── dictation.py  README.md  CLAUDE.md  LICENSE  requirements.txt
├── docs/        TODO · CHANGELOG · kurulum/auto-start · kalibrasyon · arsiv · <konu>-<tarih>/
├── scripts/     setup.* · tek start.vbs (yolu kendi konumundan bulur) · start.sh · VoiceDictation.app
├── tests/       (file_queue kalırsa)
├── data|veri/   GİT DIŞI · değerli · yedeklenir · yeni cihaza kopyalanır   → girdi / ses / transkript
├── .local/      GİT DIŞI · makineye özel · yeniden üretilir                → logs · models · file-queue
└── venv/        GİT DIŞI · platforma özel · yeri ve adı değişmez (CUDA DLL yolu buna bağlı)
```

| Konu | Ortak görüş | Kaynak |
|---|---|---|
| Yollar | `dictation.py` başında tek blok: `BASE_DIR = dirname(__file__)`, alt yollar buradan. Ayrı `paths.py` yok. Drive/Desktop fallback (`_ensure_writable_dir`) tamamen kalkar; yazılamayan hedef açık hata verir. | 5/5 |
| Modeller | Whisper HF önbelleğinde kalsın (`~/.cache/huggingface/hub`), `HF_HOME` taşınmasın — önbellek Qwen (7,6 GB), gliner, bert ile ortak; large-v3 büyük olasılıkla iFonzo `tools/voice`'un. Yeri belgelensin. speechbrain kopyası `.local/models/`. | 5/5 |
| Kurulum kırık | `requirements.txt` 5 paket; `pystray`+`Pillow` (Win) ve `rumps` (Mac) yok → temiz Mac kurulumunda tepsi açılışta çöker. Çözüm: tek `requirements.txt`, PEP 508 platform koşulları; `setup.*` "venv + pip install -r" düzeyine iner. | 4/5 |
| Başlatma | Üç başlatıcı var; Startup'taki dosya kısayol değil **kopya**; belgeler "vbs → bat" diyor, yanlış. `.app/main.scpt` içinde `/Users/yigitkumral/Desktop/Yazılım/VoiceDictation` sabit. Çözüm: tek `scripts/start.vbs` kendi yolunu bulur, Startup'a kısayol (`setup.bat` üretir), `main.scpt` `path to me`. | 5/5 |
| BMAD | İzlenen 1534 dosyanın 1509'u (%98) BMAD; `_bmad-output` hiç oluşmamış; 33 commit'in yalnız biri dokunmuş; global skill'lerde `bmad-*` yok (`yk-*` almış). Karar Yiğit'in. | 5/5 |
| Belgeler | 5 belgede 964 satır + Drive `index.md`; aynı bilgi 2–3 yerde; README kodla çelişiyor (lecture "diske yazılmaz" ↔ WAV yazılıyor; kurulum komutları yanlış klasör; menüde Meet yok). TechWriter belge seti: `README` (insan girişi + **tek "Yerel dosyalar" tablosu**), `CLAUDE.md` ≤80 satır, `docs/nasil-calisir.md`, `docs/kurulum.md`, `docs/TODO.md`, `docs/CHANGELOG.md`, `docs/kalibrasyon/`, `docs/arsiv/`. Bakım kuralı: yol/menü/CLI değiştiren commit aynı commit'te tabloyu günceller; teslim öncesi `grep "Drive'ım\|Meet Recordings\|RawRecords"` boş dönmeli. | 4/5 |
| Geçiş | Daemon durdur; rclone saatleri (03:00/15:00) dışında; `robocopy` ile **kopyala**, sayı/boyut doğrula (16 MD; 11 dosya / 1003,6 MB); eski MD'lerdeki "Kaynak" satırlarına dokunma; `Records/index.md`'ye "taşındı" notu; sonra Drive kopyaları hakkında karar. | Astra + yol |
| Meet girdisi | İki dosya seçici de girdi klasöründe açılır (`initialdir`, Mac `default location`) — kullanım aynı. "Dök" akışı dosyayı girdi→ses taşır (= işlendi); Meet akışı mp4'ü yerinde bırakır, WAV'ı ses'e yazar. Drive-Meet'i bilen kod yorumları/"(1) suffix" metinleri temizlenir (`:2125`, `:2199-2201`, `:2894-2896`). | yol (+Astra) |
| Yarım iş | `file_queue.py` + `tests/` + `.gitignore` `.local/` 15 Eylül 21:13'te birlikte yazılmış, commit edilmemiş, `dictation.py` import etmiyor, belge anmıyor. Hedefi iFonzo WhatsApp hattıydı; iFonzo artık bağımsız ses aracı kullanıyor (`iFonzo/README.md:63`). | 4/5 |

## 2. Ayrışmalar

| Konu | Seçenekler | Koordinatör önerisi |
|---|---|---|
| Klasör dili | TechWriter: Yiğit'in dokunduğu klasörler Türkçe `veri/{gelen,ses,transkript}`, araç klasörleri İngilizce. yapı/yol: tek kural İngilizce küçük harf `data/{inbox,audio,transcripts}` (kökte bugün hep İngilizce). Astra karışık. | **Yiğit'in kararı** (aşağıda). |
| `scripts/` mi `tools/` mu | Yalnız Astra `tools/` diyor (iFonzo benzerliği). | `scripts/` kalsın — Login Items `scripts/VoiceDictation.app` yoluna kayıtlı, yeniden adlandırma izin turunu tetikler. |
| Log konumu | `.local/logs/` (Astra, yapı, ortam) ↔ `logs/` kalsın (yol, TechWriter). | `.local/logs/` — "atılabilir" sınıfı tek yerde toplanır; tek satır (`_LOG_DIR`). |
| Env override | yol: tek `VOICEDICTATION_DATA_DIR`; Astra: hiç. | Tek değişken kalsın — 1 satır maliyet, başka disk/cihaz esnekliği. |
| CHANGELOG biçimi | Astra `docs/changelog/` günlük dosyalar (iFonzo gibi); TechWriter tek dosya (ayda ~1 kayıt). | Tek dosya. |

## 3. Tek ajanın bulduğu, ama önemli noktalar

- **Mac yol hatası (yol):** `posixpath.join(r"G:\Drive'ım\Records", …)` Mac'te göreli yol üretir → çıktılar çalışma klasöründe `G:\Drive'ım\Records/` adlı bir klasöre yazılır, fallback hiç devreye girmez. Yeni yapıda kendiliğinden kalkar.
- **Loglar tam diktasyon metni tutuyor (ortam):** `[OK] >> {msg}` (`:3198`), `[CHECK] Duydum:` (`:3262`), canlı cümleler (`:1795`) INFO seviyesinde; 157 dosya, sınırsız (`backupCount=0`), rclone ile Drive'a gidiyor. `file_queue.py:8` "transkript log'a yazılmaz" der — iki politika çelişiyor. Öneri: yalnız karakter sayısı logla, `backupCount=30`.
- **Sonar bağımlılığı (TechWriter + yol):** `Records/RawRecords`'taki 2 Sonar mp4'ünü Sonar'ın 4 belgesi kaynak sayıyor; Sonar'ın `kayit-notu` skill'i bu klasöre **yazıyor**. Taşınırsa Sonar kırılır.
- **`.codex/config.toml` git'te izleniyor (yapı + ortam):** `C:\Python314` ve iFonzo mutlak yolları; Mac'te her `git pull` uyuşmazlık. Git'ten çıkar, ignore'a al, `sync-claude.py` üretsin.
- **`.gitignore` hataları (yapı + ortam):** genel `settings.json` kuralı `.claude/settings.json`'ı da yutuyor; `.dictation.log`, `.dictation.pid`, `pretrained_models/` ölü.
- **Aynı ada üstüne yazma (Astra + yol):** lecture WAV/MD (`:1928`, `:1944`) ve "dök" MD'si (`:1634`) aynı adlı dosyayı ezer; yalnız Meet akışı ve "dök" sesi zaman eki ekler. Veri tek yere toplanınca risk büyür.
- **venv (ortam):** Python 3.14.2 (README "3.10+"); 2,8 GB'ın 1,7 GB'ı nvidia; diarize paketleri (~700 MB) kurulu ama listede yok; `ImageHash`, `imageio_ffmpeg` kullanılmıyor. Her saatlik toplantı ~115 MB WAV ekler.
- **Ölü kod (yol):** `_get_desktop_path`, `_get_lectures_dir`, `_pick_file_and_meet_dictate` (diarize, çağıran yok), `_get_hf_token` (→ `.env` şu an gereksiz), `calibration/README.md`'deki yazılmamış `--calibrate` akışı (Astra).
- **Cihazlar arası (yol + ortam):** Drive `Records/` bugün Win↔Mac transkript eşitlemesini de sağlıyordu; `data/` git dışı olduğu için iki cihaz ayrışır. Mac'te klasör `Yazılım` (ı), Windows'ta `Yazilim`.

## 4. Kararlar

### Önerilen varsayılanlar (itiraz yoksa plana böyle girer)
1. Hedef ağaç §1'deki gibi; `scripts/` adı kalır; loglar `.local/logs/`; tek env `VOICEDICTATION_DATA_DIR`.
2. `requirements.txt` PEP 508 ile tamamlanır; `setup.*` sadeleşir; README'ye denenen Python sürümü yazılır.
3. Tek `scripts/start.vbs` + Startup kısayolu; `main.scpt` `path to me`; kök `start.*` ve kök `dictation.log`, `.playwright-mcp/`, `__pycache__/` silinir.
4. `.codex/config.toml` git'ten çıkar; `.gitignore` yeniden yazılır (`venv/ __pycache__/ *.py[co] .local/ data/ .env .mcp.json .codex/config.toml .claude/settings.local.json .playwright-mcp/ .DS_Store Thumbs.db .vscode/ .idea/`).
5. Belge seti TechWriter önerisi; CHANGELOG tek dosya; `.agents/legacy-instructions/` özü changelog'a, dosya silinir.
6. Geçiş: kopyala → doğrula → sonra sil; eski MD "Kaynak" satırlarına dokunulmaz; `Records/index.md`'ye taşındı notu.
7. Aynı ada üstüne yazma tek yardımcı fonksiyonla düzeltilir (küçük, davranışı korur: ad çakışırsa zaman eki).
8. Yedek filtresi: `- /VoiceDictation/.local/` eklenir, `data/` yedekte kalır (`_yedek-config` tarafında, ayrı onay).
9. HF önbelleğinde `medium` + `small` (1,9 GB) silinebilir; `large-v3` iFonzo'da doğrulanmadan silinmez.

### Gerçekten Yiğit'in kararı
- **K1 Klasör dili:** `data/{inbox,audio,transcripts}` mı, `veri/{gelen,ses,transkript}` mi?
- **K2 BMAD:** `_bmad/` + `.claude/skills/bmad-*` + `.agents/skills/` + CLAUDE.md §2 bu projeden çıksın mı? (IhalePilot, UYAPEsatis, Zugzwang'da da kurulu — bu karar yalnız VoiceDictation için.)
- **K3 `file_queue.py` + `tests/`:** koda bağlansın, ayrı branch'e alınsın, yoksa silinsin?
- **K4 Diarize/speechbrain:** ölü kod + `models/` (85 MB) + ~700 MB paket: "ileride opt-in" olarak kalsın mı, kaldırılsın mı?
- **K5 Sonar dosyaları:** Drive `Records/` Sonar'a kalsın, VoiceDictation yalnız kendi 9 ses dosyası + 16 MD'sini alsın? (Öneri: evet.) Taşıma doğrulandıktan sonra Drive'daki VoiceDictation kopyaları silinsin mi?
- **K6 Win ↔ Mac kullanım modeli:** tek yönlü göç mü, paralel kullanım mı? Paralelse `data/` eşitlemesi için ayrı çözüm gerekir (Drive eşitlemesi kalkıyor). Mac'te `Yazılım` yedekleniyor mu?
- **K7 Log içeriği:** tam diktasyon metni loglanmaya devam mı? Saklama 30 gün mü? Eski 157 log arşiv mi, silme mi?
- **K8 Meet mp4'leri girdi klasöründe:** işlendikten sonra yerinde kalsın (bugünkü davranış, elle temizlik) mı, ses klasörüne taşınsın mı?
- **K9 Yeni MD'lerde "Kaynak" satırı:** repo-göreli yol mu (Mac'te de anlamlı; küçük çıktı değişikliği), mutlak yol mu?

## 5. Sonraki adım
Kararlar netleşince: yapılacaklar planı (iş paketleri, dosya sahipleri, kabul kontrolleri, ana dala alınma sırası) plan modunda hazırlanır; uygulama daemon kapalıyken, rclone saatleri dışında, commit onayıyla.
