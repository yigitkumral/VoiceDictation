# Kurulum ve otomatik başlatma

Bu belge VoiceDictation'ı kurmayı ve taşımayı anlatır. Normal kod güncellemesinde yeniden başlatmak yeterlidir; 24 Ekim 2026 klasör değişikliği için aşağıdaki geçiş ayrıca gerekir.

## Eski klasör düzeninden geçiş

Windows ve Mac dosya/ortam geçişi tamamlandı (24–25 Ekim 2026). Başka eski kurulumlarda yalnız `git pull` yapıp eski `.app` ile başlatmak yeterli değildir; aşağıdaki adımlar uygulanır. Mac'in gerçek kullanım kabulü TODO dosyasında takip edilir.

1. Daemon'ı normal menüsünden kapat; ona ait model sürecinin de kapandığını doğrula. Git'teki yerel değişiklikleri karşılaştırıp koru.
2. Repo kökündeki eski `data/` klasörünü `.local/data/` altına taşı. Hedef zaten varsa birleştirme veya üzerine yazma yapma; önce dosya envanterlerini karşılaştır. Kopyalama sürüyorsa bitmesini bekle. `.env` varsa `.local/.env` konumuna taşı.
3. Yeni `.local/venv/` ortamını `dev/scripts/setup.sh` (Mac) veya `dev/scripts/setup.bat` (Windows) ile kur. Eski ortamı yeni kurulum doğrulanana kadar koru; sanal ortamlar yalnız klasör adı değiştirilerek güvenle taşınmaz.
4. `.local/venv/bin/python -B -m unittest discover -s dev/tests` ile Mac testlerini çalıştır; Windows'ta `bin/python` yerine `Scripts/python` kullan. Veri dosyalarının ad, sayı ve boyutlarını doğrula.
5. Mac'te eski `.app` paketini yedekle; `bash dev/scripts/build-mac-app.sh` ile `.local/VoiceDictation.app` üret. Bu betik var olan uygulamanın üzerine yazmaz. Login Items'ı yeni yola geçir; gerekirse yeni uygulamanın izinlerini macOS arayüzünden ver. Trackpad için `bash dev/scripts/build-mac-trackpad.sh` çalıştır.
6. Yeni başlatıcıyla tek daemon aç; ses, hareket, kayıt ve yapıştırmayı doğrula. Bundan sonra eski ortam ve kullanılmayan başlatıcı kopyaları kaldırılabilir. Windows Startup kısayolunun yeni hedefi `dev/scripts/start.vbs` olur.

Başlatıcılar Python önbelleğini `.local/__pycache__/` altında toplar. `.local/data/` değerli kişisel veridir; `.local/` klasörünü bütünüyle önbellek sayıp silme. 24 Ekim Windows kontrolünde mevcut rclone filtresi yeni veri yolunu dışlamıyordu.

## Gereksinimler

- **Python 3.12 veya üstü.** Windows venv'i 3.14.2 ile test edildi.
- **Windows:** CUDA destekli NVIDIA GPU önerilir; CUDA kütüphaneleri pip ile gelir. GPU yoksa uygulama CPU ile çalışır.
- **macOS:** Apple Silicon, [Homebrew](https://brew.sh/) (portaudio için) ve Xcode komut satırı araçları (`osacompile`, `codesign`).

### dev/requirements.txt

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
dev\scripts\setup.bat
```

`setup.bat` sırayla şunları yapar:

1. `.local\venv\` yoksa oluşturur.
2. `.local\venv\Scripts\python -m pip install -r dev/requirements.txt` ile CUDA ve tepsi paketleri dahil tüm bağımlılıkları kurar. `pip.exe` yerine `python -m pip` kullanılır, çünkü `pip.exe` venv'in eski mutlak yolunu içinde taşır.
3. Startup klasörüne `VoiceDictation.lnk` kısayolunu yazar (varsa üstüne yazar).
   - Hedef: `wscript.exe`. `.vbs` dosya ilişkilendirmesi değişse bile betik editörde açılmaz, çalışır.
   - Argüman: `"<repo>\dev\scripts\start.vbs"`. Çalışma dizini: repo kökü.
4. Startup klasöründe eski bir `start.vbs` kopyası bulursa uyarır. O kopyayı elle sil. İkisi birlikte durursa daemon iki kez başlatılmaya çalışılır ve PID kilidi ikincisini reddeder.
5. Veri (`.local\data\`) ve log (`.local\logs\`) yerlerini yazdırır.

Kısayolu elle eklemek için: `Win+R` → `shell:startup` → Yeni → Kısayol → `wscript.exe "<repo>\dev\scripts\start.vbs"`.

`dev/dictation.py` açılışta `.local\venv\Lib\site-packages\nvidia\*\bin` klasörlerini DLL arama yoluna ekler. Bu yüzden venv'in adı ve yeri değişmemeli.

### Başlatma

| Dosya | Görevi |
|---|---|
| `dev\scripts\start.vbs` | Konsolsuz başlatıcı. Repo kökünü kendi konumundan bulur (`dev\scripts\` klasörünün iki üstü) ve `.local\venv\Scripts\pythonw.exe -m dev.dictation` komutunu çalıştırır. venv yoksa uyarı penceresi açar. |
| Startup → `VoiceDictation.lnk` | Oturum açılışında `start.vbs`'i çalıştırır. |
| `dev\scripts\start.bat` | Konsollu başlatıcı: küçültülmüş bir konsolda `python -u -m dev.dictation` çalıştırır. Program çökerse pencere kapanır; hatayı görmek için bir terminalde `.local\venv\Scripts\python -m dev.dictation` çalıştır. |

Repo başka bir klasöre taşınırsa kısayolu yenilemek için `dev\scripts\setup.bat` dosyasını yeniden çalıştır; komut kurulu paketleri atlar.

## macOS

### Kurulum

```bash
git clone https://github.com/yigitkumral/VoiceDictation.git
cd VoiceDictation
./dev/scripts/setup.sh
```

`setup.sh` önce portaudio'yu (`brew install portaudio`) kurar, sonra venv'i oluşturur ve `pip install -r dev/requirements.txt` ile `mlx-whisper` ve `rumps` dahil tüm bağımlılıkları yükler. Elle başlatmak için `./dev/scripts/start.sh` kullan. Bu komut Terminal'in mevcut izinleriyle çalışır.

### Login'de başlatma: `.local/VoiceDictation.app`

**Neden AppleScript uygulaması:**

- macOS Tahoe'da LaunchAgent, mikrofon izni penceresini arka planda gösteremez ve takılır.
- Login Items'a eklenen `start.sh` çalıştırılmaz, TextEdit ile açılır.
- Ad-hoc imzalı kabuk betiği uygulamasını TCC sessizce reddeder.
- `osacompile` ile derlenen AppleScript uygulaması Otomasyon izin kategorisinde çalışır.

Uygulama yalnız başlatıcıdır ve her açılışta repodaki `dev/dictation.py`'yi çalıştırır. Betik, `path to me` ile kendi konumunu bulur:

```applescript
set appPath to POSIX path of (path to me)
do shell script "cd \"$(dirname " & quoted form of appPath & ")/..\" && nohup .local/venv/bin/python -u -m dev.dictation > .local/logs/applet.log 2>&1 &"
```

- **Yol çözümü:** `dirname`, `.app/` sonundaki eğik çizgiyi yok sayar ve `…/.local` döndürür; `/..` repo köküne çıkar. Repo yolu uygulamanın içine yazılmaz, bu yüzden `Yazılım` gibi Türkçe karakterli ya da boşluklu yollar ve taşınan klasörler sorun çıkarmaz.
- **Eski `.app`:** 30 Eylül 2026'dan önceki sürümün içinde sabit bir repo yolu vardı ve içindeki `Yazılım`
  yazımı ASCII `Yazilim` klasörüyle eşleşmediği için applet `cd` adımında sessizce kopuyordu. Depodaki
  uygulama artık yoldan bağımsızdır; yine de klasör taşınırsa ya da imza yenilenirse aşağıdaki adımlar geçerlidir.
- **Yeniden derlemekten kaçın.** Her `osacompile` + ad-hoc imza yeni bir kod kimliği üretir; macOS izin
  kaydını imzaya bağladığı için Input Monitoring ve Accessibility listelerindeki eski girdiler ölü kalır ve
  uygulama izinli görünmesine rağmen çalışmaz. Belirti: `applet.log` içinde
  `This process is not trusted!`. Çözüm, iki listedeki tüm eski girdileri **−** ile silip `.app`'i tek
  seferde yeniden eklemektir. Aynı uygulama listelerde hem `applet` (ikili adı) hem `VoiceDictation`
  (paket adı) olarak görünebilir; ikisi de aynı şeydir, ikisini de temizle.

**Uygulamayı derle** (Mac'te, repo kökünde):

```bash
bash dev/scripts/build-mac-app.sh
```

- **Dock:** `LSUIElement=true` uygulamayı Dock'ta gizler.
- **İzinler:** Bundle kimliği eskisiyle aynı tutulur (`com.voicedictation.launcher`). Buna rağmen yeni ad-hoc imza nedeniyle macOS izinleri yeniden sorabilir.
- **Git:** Derlenmiş `.app` yereldir ve Git dışıdır. AppleScript kaynağı ile derleme betiği `dev/scripts/` altında izlenir. Mevcut `.app` varsa derleme betiği üzerine yazmaz.

**Login Items'a ekle:**

1. System Settings → General → Login Items & Extensions.
2. Eski bir girdi varsa (`start.sh`, eski `.app` ya da LaunchAgent) **−** ile kaldır.
3. "Open at Login" altında **+** → `Cmd+Shift+G` → repodaki `.local/VoiceDictation.app` yolunu seç → **Open**.
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
2. **Yalnız `.local/data/`** klasörünü aynı yere kopyala. Kaynak eski cihaz ya da `Yazilim` yedeği olabilir.
3. `./dev/scripts/setup.sh` (macOS) veya `dev\scripts\setup.bat` (Windows) çalıştır. Bu adım venv'i kurar; Windows'ta Startup kısayolunu da yazar. Eski bir venv varsa paketler `dev/requirements.txt` alt sınırlarına yükseltilir.
4. İlk açılışta Whisper turbo modeli `~/.cache/huggingface/hub/` klasörüne iner; bu adım bir kez internet ister. macOS'ta model `mlx-community/whisper-turbo`, boyutu yaklaşık 1,6 GB. `.local/` klasörü kendiliğinden oluşur.
5. Ajan ayarlarını yeniden oluştur:
   - `.mcp.json` Git'le gelir; sır gerekirse değeri Git dışı `.local/.env`'e yaz (uygulamanın yerel ayar yükleyicisi okur).
   - `.codex/config.toml` dosyasını iFonzo'nun `docs/tools-global/codex/sync-claude.py --apply` komutuyla üret.
6. macOS'ta `.app`'i derle, Login Items'a ekle ve dört izni ver (yukarıda).
7. Mac'te ilk kez çalıştırıyorsan [TODO.md](TODO.md) dosyasındaki "Mac'te ilk oturum" listesini uygula.

Kopyalanmayanlar ve nedenleri:

- `.local/venv/` platforma özeldir.
- `.local/` bu makineye özeldir: loglar ve modeller.
- `.local/.env` isteğe bağlıdır; yalnız bir ortam değişkeni gerekiyorsa elle oluşturulur.

## Sorun giderme

- **Önce log:** `.local/logs/YYYY-MM-<Ay>.log` (örn. `2026-09-Eylul.log`). Çıktıyı canlı görmek için programı bir terminalde çalıştır: `.local\venv\Scripts\python -m dev.dictation` veya `.local/venv/bin/python -m dev.dictation`.
- **"venv bulunamadi" uyarısı (Windows):** `start.vbs` venv'i bulamadı; önce `dev\scripts\setup.bat` çalıştır.
- **"Daemon zaten çalışıyor":** `.local/logs/dictation.pid` canlı bir süreci gösteriyor demektir. Tray → Çıkış ile kapat. Süreç ölmüşse eski PID dosyası yok sayılır.
- **CUDA bulunamadı:** Uygulama CPU ile çalışmaya devam eder. `pip install -r dev/requirements.txt` komutunun `nvidia-*` paketlerini kurduğunu kontrol et.
- **Uygulama iki kez başlıyor (Windows):** Startup klasöründe `VoiceDictation.lnk` dışında eski bir `start.vbs` kopyası olup olmadığına bak.
- **macOS'ta kısayol tuşu veya yapıştırma çalışmıyor:** İzin tablosuna bak; genellikle Giriş İzleme veya Erişilebilirlik eksiktir.
