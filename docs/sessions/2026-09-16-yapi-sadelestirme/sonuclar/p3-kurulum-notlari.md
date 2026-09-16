# P3 — Kurulum ve başlatma notları (`opus-ortam`, 16 Eylül 2026)

Bu turda değişen dosyalar: `requirements.txt`, `scripts/setup.bat`, `scripts/setup.sh`, yeni `scripts/start.vbs`.
`scripts/start.bat` ve `scripts/start.sh` aynen kaldı. Commit atılmadı; betikler gerçek ortamda çalıştırılmadı.
Aşağıdaki A–F bölümleri P4'ün `docs/kurulum.md` dosyasına alacağı ham metindir.

## Doğrulama (bu tur)

- **Windows:** `venv\Scripts\python -m pip install -r requirements.txt --dry-run` çözüldü. Bütün paketler "Requirement already satisfied" verdi, "Would install" satırı çıkmadı. `rumps` ve `mlx-whisper` "markers … don't match" ile atlandı.
- **macOS (yaklaşık):** Windows'tan `--platform macosx_14_0_arm64 --only-binary=:all:` ile denendi; Python 3.12'de de 3.14'te de çözüldü. Seçilen sürümler: mlx 0.32.2, mlx-whisper 0.4.3, numpy 2.5.3, numba 0.67.0, torch 2.14.0 (mlx-whisper'ın bağımlılığı), ctranslate2 4.8.2.
  - `rumps` yalnız sdist yayımlandığı için bu denemeye alınamadı; yerine tek bağımlılığı `pyobjc-framework-Cocoa` denendi ve çözüldü. Gerçek kurulumda `rumps` kaynaktan derlenir; saf Python olduğu için sorun beklenmez.
  - Geçişli `darwin` koşulları (ör. pynput → pyobjc Quartz) Windows'tan değerlendirilemez. Kesin doğrulama Mac'te yapılacak.
- **`start.vbs`:** Scratchpad'de, boşluklu bir sahte repo yolunda, `Run`/`MsgBox` satırları `Echo`'ya çevrilmiş birebir kopyayla ve başka bir çalışma dizininden denendi.
  - venv yokken uyarı verip 1 koduyla çıktı.
  - venv varken şu komutu üretti: `"<repo>\venv\Scripts\pythonw.exe" dictation.py`. Çalışma dizini repo kökü oldu.
- **`setup.bat`:** pip adımı taklit edilerek, APPDATA scratchpad'e yönlendirilmiş bir kopyayla uçtan uca çalıştırıldı.
  - `.lnk` dosyası geri okundu: hedef `C:\Windows\System32\wscript.exe`, argüman `"<repo>\scripts\start.vbs"`, çalışma dizini repo kökü.
  - Kısayol yazılamayınca UYARI satırı çıktı.
  - Eski `start.vbs` kopyası varken uyarı verdi.
  - Gerçek Startup klasörüne dokunulmadı (`Ollama.lnk`, `desktop.ini`, `start.vbs` aynen duruyor).
- `grep "Drive\|RawRecords"` araması `requirements.txt` ve `scripts/*` içinde sonuç vermedi.

---

## A. macOS — `main.scpt` (repo yolundan bağımsız)

`.app` dosyası `scripts/` altında durur. Kendi konumunu `path to me` ile bulur; bir üst klasör repo köküdür. Bugünkü `.app` içinde `/Users/yigitkumral/Desktop/Yazılım/VoiceDictation` yolu sabit yazılı, bu yüzden klasör taşınınca bozulur.

```applescript
set appPath to POSIX path of (path to me)
do shell script "cd \"$(dirname " & quoted form of appPath & ")/..\" && nohup venv/bin/python -u dictation.py > /dev/null 2>&1 &"
```

`dirname`, `.app/` sonundaki eğik çizgiyi yok sayar ve `…/scripts` döndürür; `/..` ile repo köküne çıkılır. Türkçe karakterli yollar (`Yazılım`) ve boşluk içeren yollar `quoted form` ile güvenlidir.

## B. macOS — `.app` derleme (Mac'te, repo kökünde)

```bash
cat > /tmp/vd-main.applescript <<'EOF'
set appPath to POSIX path of (path to me)
do shell script "cd \"$(dirname " & quoted form of appPath & ")/..\" && nohup venv/bin/python -u dictation.py > /dev/null 2>&1 &"
EOF
rm -rf scripts/VoiceDictation.app
osacompile -o scripts/VoiceDictation.app /tmp/vd-main.applescript
P=scripts/VoiceDictation.app/Contents/Info.plist
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$P" || /usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$P"
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.voicedictation.launcher" "$P"
codesign --sign - --force --deep scripts/VoiceDictation.app
```

- `LSUIElement=true`: uygulama Dock'ta görünmez.
- Bundle kimliği eskisiyle aynı tutulur (`com.voicedictation.launcher`). Buna rağmen yeni ad-hoc imza nedeniyle TCC izinleri yeniden sorulabilir; C bölümüne bakın.
- `.app` git'te izlenir. Yeniden derleme bir ikili dosya değişikliği olarak commit edilir.

## C. macOS — Login Items ve 4 izin

**Neden AppleScript `.app`:** macOS Tahoe'da diğer yollar çalışmadı:
- LaunchAgent: mikrofon izni diyaloğu arka planda gösterilemiyor ve süreç askıda kalıyor.
- Login Items'a eklenen `start.sh`: TextEdit ile açılıyor.
- Ad-hoc imzalı shell-script uygulaması: TCC sessizce reddediyor.

AppleScript `.app` ise `Automation` kategorisinde olduğu için çalışıyor.

1. System Settings → General → Login Items & Extensions → "Open at Login" → **+** → `Cmd+Shift+G` → `<repo>/scripts/VoiceDictation.app`.
2. İlk açılışta **Mikrofon** ve **Otomasyon** izinlerini ver.
3. Privacy & Security'de iki izni elle aç:
   - **Input Monitoring** → `applet`: Caps Lock kısayolu için.
   - **Accessibility** → `applet`: Cmd+V ve Enter göndermek için.
4. VoiceDictation'ı bir kez yeniden başlat.

| İzin | Eksikse ne bozulur |
|---|---|
| Mikrofon | Hiç kayıt yapılamaz |
| Otomasyon | `.app` hata verir, uygulama başlamaz |
| Input Monitoring | Caps Lock algılanmaz (yalnız wake word çalışır) |
| Accessibility | Metin panoda kalır, yapıştırılmaz |

Eski denemelerden TCC'de "VoiceDictation" gibi bayat kayıtlar kalabilir; bunlar **−** ile silinir. Etkin kayıt `applet`'tir. Elle başlatmak için: `./scripts/start.sh`.

## D. Windows — kısayol mantığı ve `setup.bat`

- **Tek kaynak:** git'te izlenen `scripts/start.vbs`. Repo kökünü kendi konumundan bulur ve `venv\Scripts\pythonw.exe dictation.py` komutunu gizli pencerede çalıştırır. venv yoksa uyarı kutusu gösterir.
- **Startup klasöründe kopya değil, kısayol durur:** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VoiceDictation.lnk`.
  - Hedef: `wscript.exe`. `.vbs` dosya ilişkilendirmesi değiştirilmiş olsa bile betik editörde açılmaz, çalışır.
  - Argüman: `"<repo>\scripts\start.vbs"`. Çalışma dizini: repo kökü.
  - Kod `git pull` ile güncellenir; kısayol bir kez kurulur ve bir daha dokunulmaz.
- **`scripts\setup.bat` sırasıyla şunları yapar:**
  1. venv yoksa `python -m venv venv` ile oluşturur.
  2. `venv\Scripts\python -m pip install -r requirements.txt` çalıştırır. CUDA ve tepsi paketleri de buradan gelir. `pip.exe` yerine `python -m pip` kullanılır, çünkü `pip.exe` venv'in eski mutlak yolunu içinde taşır.
  3. Kısayolu yazar; kısayol varsa üstüne yazar.
  4. Startup'ta eski `start.vbs` kopyası varsa uyarır.
  5. Veri (`data\`) ve log (`.local\logs\`) yerlerini yazdırır.
- **Elle kurulum:** `Win+R` → `shell:startup` → Yeni kısayol → `wscript.exe "<repo>\scripts\start.vbs"`.
- **Konsollu hata ayıklama:** `scripts\start.bat`, küçültülmüş bir konsolda `python -u dictation.py` çalıştırır.
- **Geçiş (P0-B4):** Startup'taki eski `start.vbs` kopyası (29 Mart, sabit yollu) silinir. Yerine `setup.bat` çalıştırılır ya da kısayol elle eklenir. İkisi birlikte durursa daemon iki kez başlatılmaya çalışılır; PID kilidi ikincisini reddeder.

## E. `requirements.txt` platform koşulları

- Tek dosyadır. Satır sonundaki `; sys_platform == "win32"` / `"darwin"` koşulu (PEP 508) sayesinde pip her platformda yalnız ilgili satırları kurar.
- **Ortak:** faster-whisper, sounddevice, numpy, pynput, pyperclip. faster-whisper Mac'te de gerekir, çünkü MLX yolundaki Silero VAD ön filtresi ondan gelir.
- **Windows:**
  - `pystray` + `Pillow`: tepsi simgesi.
  - `nvidia-cublas-cu12` + `nvidia-cudnn-cu12<10`: CUDA. ctranslate2 4.x, cuDNN 9 ister.
  - `dictation.py` açılışta `venv\Lib\site-packages\nvidia\*\bin` klasörlerini DLL yoluna ekler. Bu yüzden venv'in adı ve yeri değişmemeli.
- **macOS:** `rumps` (menü çubuğu) + `mlx-whisper` (Apple Silicon GPU; torch da onunla gelir). `setup.sh` ayrıca Homebrew ile `portaudio` kurar.
- **Sürüm alt sınırları** 16 Eylül'deki Windows venv'inden alındı (`>=`, sabitleme yok). `rumps` ve `mlx-whisper` için sınır PyPI'daki güncel seriden alındı.
- **Python:** 3.14.2 ile test edildi; 3.12+ önerilir. numpy 2.4 en az 3.11 ister.
- **Opsiyonel:** speechbrain, torch ve scikit-learn (konuşmacı ayırma, uyuyan özellik) yorum satırındadır; gerekirse elle kurulur.

## F. MacBook'a taşıma kontrol listesi

- **Kopyalanır:** yalnız `data/` (`inbox/`, `audio/`, `transcripts/`). Kaynak: Windows makinesi ya da `Yazilim` Drive yedeği. Cihazlar arası eşitleme yok (K6).
- **Kopyalanmaz:** `venv/` (platforma özel), `.local/` (log, model, kuyruk), `.env` (yok; HF token kullanılmıyor).
- **Yerinde yeniden üretilir:**
  1. `git clone` / `git pull`. Dosya kopyalamayla taşınırsa `.sh` dosyalarında CRLF sorunu çıkabilir; aşağıdaki açık noktalara bakın.
  2. `./scripts/setup.sh`: portaudio, venv ve bağımlılıklar. Nisan'dan kalan bir venv varsa `numpy` gibi paketler alt sınıra yükseltilir.
  3. İlk açılışta MLX turbo modeli (`mlx-community/whisper-turbo`, ~1,6 GB) `~/.cache/huggingface/hub/` altına iner; bir kez internet gerekir.
  4. `.mcp.json`, `.mcp.json.example` dosyasından Mac yoluyla üretilir.
  5. `.codex/config.toml`, `sync-claude.py --apply` ile üretilir (git dışı).
  6. `.app` B bölümündeki gibi derlenir. Login Items ve 4 izin C bölümündeki gibi verilir.
  7. `docs/TODO.md` içindeki "Mac'te ilk oturum" doğrulama listesi uygulanır.

---

## Açık noktalar (koordinatör / Yiğit)

1. **`scripts/start.bat` penceresi:** `cmd /c` kullandığı için çökme anında konsol kapanır ve hata görünmez. Brif "içeriği doğru" dediği için dokunulmadı. Hata ayıklamada `cmd /k` daha kullanışlı olur; karar sizde.
2. **`.gitattributes` yok ve `core.autocrlf=true`:** Windows'ta `.sh` dosyaları CRLF ile açılıyor. Repo Mac'e git ile değil dosya kopyalayarak taşınırsa shebang bozulur. Öneri: `*.sh text eol=lf`, `*.bat text eol=crlf`, `*.vbs text eol=crlf`. Bu dosya P2'nin ya da koordinatörün alanı.
3. **README hâlâ "Python 3.10+" diyor** (P4): "3.12+ önerilir, 3.14.2 ile test edildi" olmalı. Ayrıca README'de `setup.bat`/`setup.sh` repo kökünde çalıştırılıyormuş gibi anlatılıyor; doğrusu `scripts\setup.bat` ve `./scripts/setup.sh`.
4. **Mac bağımlılık çözümü yaklaşık:** kesin doğrulama Mac'teki ilk oturumda yapılmalı. TODO listesine "`./scripts/setup.sh` temiz venv'de" maddesi eklenebilir.
