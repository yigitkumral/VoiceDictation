# P3 — Kurulum ve başlatma (`opus-ortam`)

Önce `plan.md` ve `kararlar.md`'yi oku (aynı klasör). Kendi analizin `sonuc-ortam.md` temel alındı. **Dosyaların:** `requirements.txt`, `scripts/setup.bat`, `scripts/setup.sh`, `scripts/start.vbs` (yeni), `scripts/start.bat`, `scripts/start.sh` ve not dosyan `docs/yapi-sadelestirme-2026-09-16/p3-kurulum-notlari.md`. Başka dosyaya dokunma (README/CLAUDE/docs → P4; `dictation.py` → P1). Commit yok. Daemon çalışıyor: `start.vbs`/`start.bat`/`setup.*` **çalıştırma** (P0-B'de koordinatör test eder), `pip install` yapma (yalnız `--dry-run`), venv'e dokunma. Startup klasörüne dokunma.

## Yapılacaklar

1. **`requirements.txt` (PEP 508 koşullu):** mevcut 5 satır + 
   `pystray; sys_platform == "win32"`, `Pillow; sys_platform == "win32"`, `nvidia-cublas-cu12; sys_platform == "win32"`, `nvidia-cudnn-cu12; sys_platform == "win32"`, `rumps; sys_platform == "darwin"`, `mlx-whisper; sys_platform == "darwin"`. Sürüm alt sınırlarını venv'deki kurulu sürümlerden türet (`venv\Scripts\pip show <paket>` ile bak; `>=` kullan, sabitleme). Diarize paketleri (`speechbrain`, `torch`, `scikit-learn`) yorum satırında "opsiyonel — konusmaci ayirma (uyuyan ozellik)". Başta 2 satır yorum: Python 3.14.2 ile test edildi (venv), 3.12+ önerilir.
2. **`scripts/setup.bat`:** venv oluştur (yoksa) + `venv\Scripts\pip install -r requirements.txt` (ayrı nvidia adımı kalkar) + Startup'a kısayol: PowerShell tek satırla `WScript.Shell` → `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VoiceDictation.lnk`, hedef `wscript.exe`, argüman `"<repo>\scripts\start.vbs"`, çalışma dizini repo kökü; varsa üstüne yazar. Sonunda kısa bilgi: log yeri `.local\logs\`, veri `data\`.
3. **`scripts/setup.sh`:** portaudio adımı kalır; venv + `pip install -r requirements.txt` (mlx-whisper artık requirements'tan gelir). Sonunda Login Items / `.app` için `docs/kurulum.md`'ye yönlendirme.
4. **`scripts/start.vbs` (yeni, izlenir):** kendi konumundan repo kökünü bulur, gizli pencerede `venv\Scripts\pythonw.exe dictation.py` çalıştırır:
   ```vbs
   Set fso = CreateObject("Scripting.FileSystemObject")
   repo = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
   Set sh = CreateObject("WScript.Shell")
   sh.CurrentDirectory = repo
   sh.Run """" & repo & "\venv\Scripts\pythonw.exe"" dictation.py", 0, False
   ```
   `scripts/start.bat` konsollu hata-ayıklama başlatıcısı olarak kalır (içeriği doğru: `cd /d "%~dp0\.."`); `start.sh` aynen.
5. **Mac notu (Windows'ta derlenemez):** `p3-kurulum-notlari.md` içine P4'ün `docs/kurulum.md`'ye alacağı metin: (a) `main.scpt` için `path to me` tabanlı, repo yolundan bağımsız AppleScript (`.app` `scripts/` altında olduğuna göre iki üst klasör repo kökü), (b) `osacompile` + `Info.plist`'e `LSUIElement=true` + `codesign --sign - --force --deep` adımları, (c) Login Items'a ekleme ve 4 TCC izni (mevcut `docs/auto-start.md`'den doğru kısımlar), (d) Windows tarafı: kısayol mantığı ve `setup.bat`'ın ne yaptığı, (e) `requirements.txt` platform koşullarının kısa açıklaması, (f) MacBook'a taşıma kontrol listesi (kopyalanan: yalnız `data/`; yeniden üretilen: venv, MLX turbo modeli ilk açılışta ~1,6 GB, `.mcp.json` `.example`'dan, `.codex/config.toml` `sync-claude.py` ile, `.app` derleme, izinler).

## Kabul

- `venv\Scripts\pip install -r requirements.txt --dry-run` Windows'ta çözülür (çıktının son satırlarını geri çağrıya ekle).
- `cscript //nologo //e:vbscript` ile **söz dizimi** kontrolü için `start.vbs`'i çalıştırma; bunun yerine `WScript.ScriptFullName` mantığını küçük bir kopya betikle (`echo` eden) scratchpad'de doğrula.
- `grep -n "Drive\|RawRecords" requirements.txt scripts/setup.bat scripts/setup.sh scripts/start.*` boş.

## Geri çağrı (tek sefer)

`SendMessage` → `to: voicedictation-67`, mesaj: `hazir: P3 — <3 satır: değişen dosyalar / dry-run sonucu / açık nokta>`. Hata verirse yalnız `herdr agent get voicedictation-scope` `idle`/`done` iken `herdr agent prompt voicedictation-scope '<aynı mesaj>'`. Sonra pane'de bekle.
