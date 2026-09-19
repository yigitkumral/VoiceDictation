# Kurulum ve otomatik başlatma

Bu belge VoiceDictation'ı bir makineye kurmayı, açılışta başlatmayı ve yeni bir cihaza taşımayı anlatır. Kurulum her makinede bir kez yapılır. Kod her açılışta repodan çalıştığı için `git pull` sonrasında ek bir adım gerekmez.

## Gereksinimler

- **Python 3.12 veya üstü.** Windows venv'i 3.14.2 ile test edildi.
- **Windows:** CUDA destekli NVIDIA GPU önerilir; CUDA kütüphaneleri pip ile gelir. GPU yoksa uygulama CPU ile çalışır.
- **macOS:** Apple Silicon, [Homebrew](https://brew.sh/) (portaudio için) ve Xcode komut satırı araçları (`osacompile`, `codesign`).

### requirements.txt

Tek dosya iki platforma da hizmet eder. Satır sonundaki PEP 508 koşulu (`; sys_platform == "win32"` ya da `"darwin"`) sayesinde pip her platformda yalnız ilgili satırları kurar. Sürüm alt sınırları (`>=`, sabitleme yok) 16 Eylül 2026'daki Windows venv'inden alındı. macOS çözümü Windows'tan yalnız yaklaşık olarak denendi; kesin doğrulama Mac'te yapılacak.

| Koşul | Paketler | Neden |
|---|---|---|
| Her platform | `faster-whisper`, `sounddevice`, `numpy`, `pynput`, `pyperclip` | STT, mikrofon, kısayol tuşu, pano. macOS'ta faster-whisper VAD ön filtresi için gerekir. |
| `sys_platform == "win32"` | `pystray`, `Pillow`, `nvidia-cublas-cu12`, `nvidia-cudnn-cu12` | Tepsi simgesi ve CUDA kütüphaneleri |
| `sys_platform == "darwin"` | `rumps`, `mlx-whisper` | Menü çubuğu ve Apple Silicon Whisper |
| Yorum satırı (isteğe bağlı) | `speechbrain`, `torch`, `scikit-learn` | Kapalı konuşmacı ayırma özelliği; gerekirse elle kurulur |

## Windows

### Kurulum

```bat
git clone https://github.com/yigitkumral/VoiceDictation.git
cd VoiceDictation
scripts\setup.bat
```

`setup.bat` sırayla şunları yapar:

1. `venv\` yoksa oluşturur.
2. `venv\Scripts\python -m pip install -r requirements.txt` ile CUDA ve tepsi paketleri dahil tüm bağımlılıkları kurar. `pip.exe` yerine `python -m pip` kullanılır, çünkü `pip.exe` venv'in eski mutlak yolunu içinde taşır.
3. Startup klasörüne `VoiceDictation.lnk` kısayolunu yazar (varsa üstüne yazar).
   - Hedef: `wscript.exe`. `.vbs` dosya ilişkilendirmesi değişse bile betik editörde açılmaz, çalışır.
   - Argüman: `"<repo>\scripts\start.vbs"`. Çalışma dizini: repo kökü.
4. Startup klasöründe eski bir `start.vbs` kopyası bulursa uyarır. O kopyayı elle sil. İkisi birlikte durursa daemon iki kez başlatılmaya çalışılır ve PID kilidi ikincisini reddeder.
5. Veri (`data\`) ve log (`.local\logs\`) yerlerini yazdırır.

Kısayolu elle eklemek için: `Win+R` → `shell:startup` → Yeni → Kısayol → `wscript.exe "<repo>\scripts\start.vbs"`.

`dictation.py` açılışta `venv\Lib\site-packages\nvidia\*\bin` klasörlerini DLL arama yoluna ekler. Bu yüzden venv'in adı ve yeri değişmemeli.

### Başlatma

| Dosya | Görevi |
|---|---|
| `scripts\start.vbs` | Konsolsuz başlatıcı. Repo kökünü kendi konumundan bulur (`scripts\` klasörünün bir üstü) ve `venv\Scripts\pythonw.exe dictation.py` komutunu çalıştırır. venv yoksa uyarı penceresi açar. |
| Startup → `VoiceDictation.lnk` | Oturum açılışında `start.vbs`'i çalıştırır. |
| `scripts\start.bat` | Konsollu başlatıcı: küçültülmüş bir konsolda `python -u dictation.py` çalıştırır. Program çökerse pencere kapanır; hatayı görmek için bir terminalde `venv\Scripts\python dictation.py` çalıştır. |

Repo başka bir klasöre taşınırsa kısayolu yenilemek için `scripts\setup.bat` dosyasını yeniden çalıştır; komut kurulu paketleri atlar.

## macOS

### Kurulum

```bash
git clone https://github.com/yigitkumral/VoiceDictation.git
cd VoiceDictation
./scripts/setup.sh
```

`setup.sh` önce portaudio'yu (`brew install portaudio`) kurar, sonra venv'i oluşturur ve `pip install -r requirements.txt` ile `mlx-whisper` ve `rumps` dahil tüm bağımlılıkları yükler. Elle başlatmak için `./scripts/start.sh` kullan. Bu komut Terminal'in mevcut izinleriyle çalışır.

### Login'de başlatma: `scripts/VoiceDictation.app`

**Neden AppleScript uygulaması:**

- macOS Tahoe'da LaunchAgent, mikrofon izni penceresini arka planda gösteremez ve takılır.
- Login Items'a eklenen `start.sh` çalıştırılmaz, TextEdit ile açılır.
- Ad-hoc imzalı kabuk betiği uygulamasını TCC sessizce reddeder.
- `osacompile` ile derlenen AppleScript uygulaması Otomasyon izin kategorisinde çalışır.

Uygulama yalnız başlatıcıdır ve her açılışta repodaki `dictation.py`'yi çalıştırır. Betik, `path to me` ile kendi konumunu bulur:

```applescript
set appPath to POSIX path of (path to me)
do shell script "cd \"$(dirname " & quoted form of appPath & ")/..\" && nohup venv/bin/python -u dictation.py > /dev/null 2>&1 &"
```

- **Yol çözümü:** `dirname`, `.app/` sonundaki eğik çizgiyi yok sayar ve `…/scripts` döndürür; `/..` repo köküne çıkar. Repo yolu uygulamanın içine yazılmaz, bu yüzden `Yazılım` gibi Türkçe karakterli ya da boşluklu yollar ve taşınan klasörler sorun çıkarmaz.
- **Eski `.app`:** Repodaki sürümün içinde eski, sabit bir repo yolu var. Mac'teki ilk oturumda uygulamayı aşağıdaki adımlarla yeniden derle.

**Uygulamayı derle** (Mac'te, repo kökünde):

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

- **Dock:** `LSUIElement=true` uygulamayı Dock'ta gizler.
- **İzinler:** Bundle kimliği eskisiyle aynı tutulur (`com.voicedictation.launcher`). Buna rağmen yeni ad-hoc imza nedeniyle macOS izinleri yeniden sorabilir.
- **Git:** `.app` git'te izlenir; yeniden derlenmiş uygulama ikili dosya değişikliği olarak commit edilir.

**Login Items'a ekle:**

1. System Settings → General → Login Items & Extensions.
2. Eski bir girdi varsa (`start.sh`, eski `.app` ya da LaunchAgent) **−** ile kaldır.
3. "Open at Login" altında **+** → `Cmd+Shift+G` → repodaki `scripts/VoiceDictation.app` yolunu seç → **Open**.
4. Oturumu kapatıp aç ve izin pencerelerini onayla (aşağıda).

Eski bir LaunchAgent kurulumu varsa kaldır:

```bash
launchctl bootout gui/$(id -u)/com.voicedictation.app
rm -f ~/Library/LaunchAgents/com.voicedictation.app.plist
```

### macOS izinleri (dördü de zorunlu)

| İzin | Nereden verilir | Eksikse ne bozulur |
|---|---|---|
| Mikrofon | İlk açılışta çıkan pencere | Kayıt yapılamaz, transkript boş kalır |
| Otomasyon | İlk açılışta çıkan pencere | `.app` hata verir, uygulama başlamaz |
| Giriş İzleme (Input Monitoring) | System Settings → Privacy & Security → Input Monitoring → `applet` | Caps Lock kısayolu algılanmaz; yalnız wake word çalışır |
| Erişilebilirlik (Accessibility) | System Settings → Privacy & Security → Accessibility → `applet` | Metin panoda kalır; yapıştırma ve Enter gönderilmez |

- İzinleri verdikten sonra uygulamayı bir kez yeniden başlat.
- Listede aktif olan girdi `applet` adını taşır; eski denemelerden kalan girdileri **−** ile sil.
- `.app` yeniden derlenirse ya da taşınırsa macOS izinleri yeniden sorabilir.

## Yeni cihaza taşıma

Git kodu ve belgeleri taşır; veri git dışında kalır ve cihazlar arasında eşitlenmez. Neyin nerede durduğu README'deki [Yerel dosyalar](../README.md#yerel-dosyalar) tablosundadır.

1. Repoyu git ile klonla ya da `git pull` ile güncelle. Dosya kopyalayarak taşıma: Windows'ta `.sh` dosyaları CRLF satır sonuyla açılabilir ve macOS'ta çalışmaz.
2. **Yalnız `data/`** klasörünü aynı yere kopyala. Kaynak eski cihaz ya da `Yazilim` yedeği olabilir.
3. `./scripts/setup.sh` (macOS) veya `scripts\setup.bat` (Windows) çalıştır. Bu adım venv'i kurar; Windows'ta Startup kısayolunu da yazar. Eski bir venv varsa paketler `requirements.txt` alt sınırlarına yükseltilir.
4. İlk açılışta Whisper turbo modeli `~/.cache/huggingface/hub/` klasörüne iner; bu adım bir kez internet ister. macOS'ta model `mlx-community/whisper-turbo`, boyutu yaklaşık 1,6 GB. `.local/` klasörü kendiliğinden oluşur.
5. Ajan ayarlarını yeniden oluştur:
   - `.mcp.json` Git'le gelir; sır gerekirse değeri Git dışı `.env`'e yaz (python-dotenv ile okunur).
   - `.codex/config.toml` dosyasını iFonzo'nun `docs/tools-global/codex/sync-claude.py --apply` komutuyla üret.
6. macOS'ta `.app`'i derle, Login Items'a ekle ve dört izni ver (yukarıda).
7. Mac'te ilk kez çalıştırıyorsan [TODO.md](TODO.md) dosyasındaki "Mac'te ilk oturum" listesini uygula.

Kopyalanmayanlar ve nedenleri:

- `venv/` platforma özeldir.
- `.local/` bu makineye özeldir: loglar ve modeller.
- `.env` isteğe bağlıdır; yalnız bir ortam değişkeni gerekiyorsa elle oluşturulur.

## Sorun giderme

- **Önce log:** `.local/logs/YYYY-MM-<Ay>.log` (örn. `2026-09-Eylul.log`). Çıktıyı canlı görmek için programı bir terminalde çalıştır: `venv\Scripts\python dictation.py` veya `venv/bin/python dictation.py`.
- **"venv bulunamadi" uyarısı (Windows):** `start.vbs` venv'i bulamadı; önce `scripts\setup.bat` çalıştır.
- **"Daemon zaten çalışıyor":** `.local/logs/dictation.pid` canlı bir süreci gösteriyor demektir. Tray → Çıkış ile kapat. Süreç ölmüşse eski PID dosyası yok sayılır.
- **CUDA bulunamadı:** Uygulama CPU ile çalışmaya devam eder. `pip install -r requirements.txt` komutunun `nvidia-*` paketlerini kurduğunu kontrol et.
- **Uygulama iki kez başlıyor (Windows):** Startup klasöründe `VoiceDictation.lnk` dışında eski bir `start.vbs` kopyası olup olmadığına bak.
- **macOS'ta kısayol tuşu veya yapıştırma çalışmıyor:** İzin tablosuna bak; genellikle Giriş İzleme veya Erişilebilirlik eksiktir.
