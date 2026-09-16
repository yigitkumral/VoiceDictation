# Sonuç — Teknik Yazar (Paige / BMAD tech-writer), 16 Eylül 2026

Kapsam: belgeler ve yapının okunabilirliği. Salt okuma; kod yalnız belge doğruluğu için okundu.

## Bulgular

- **Devir testi geçilmiyor.** 5 belgede 964 satır var (`CLAUDE.md` 269, `README.md` 305, `CHANGELOG.md` 245, `TODO.md` 69, `docs/auto-start.md` 76) ve bir de Drive'da `index.md` bulunuyor. "Veri nerede, makinede ne var?" sorusunun tek bir cevabı yok. Yollar `CLAUDE.md` §1 içinde Lecture, Logging ve Auto-Start bölümlerine, README'de başka yerlere, `index.md`'de de başka bir yere dağılmış.
- **Aynı bilgi üç yerde tutuluyor:**
  - Mod akışları ve tray menüsü hem `CLAUDE.md` §1'de hem README'de yazıyor.
  - Mac izin tablosu üç kopya: README "macOS İzinleri", `auto-start.md` "ZORUNLU 4 IZIN", `CLAUDE.md` "Auto-Start".
  - Mac test listesi iki yerde: `CLAUDE.md` §0.5 ve `TODO.md`.
  - `.agents/legacy-instructions/2026-09-14-agents.md`, `CLAUDE.md`'nin eski AGENTS kopyası.
- **Kodla çelişen, eskimiş bilgiler:**
  - README "Toplantı / Ders Modu" bölümü "ses DİSKE YAZILMAZ" diyor ve çıktı yeri olarak `~/Desktop/VoiceDictation_Lectures/` veriyor. Kod ise WAV'ı `RawRecords`'a yazıyor (`dictation.py:1926`), çıktıyı da Drive'a gönderiyor (`:222`).
  - README "Dosyadan Transkript" bölümü "ses yanında `.md` + iki kopya" diyor. Kod tek MD yazıyor ve sesi taşıyor (`:1589-1617`).
  - README Kurulum `setup.bat` ve `chmod +x setup.sh start.sh` komutlarını repo kökünde gösteriyor; dosyalar `scripts/` altında.
  - README, kökteki `start.bat` ve `start.vbs` için "hazır gelir" diyor. İkisi de `.gitignore`'da, repo yolu da içlerine sabit yazılı.
  - `auto-start.md` "VBS, `start.bat`'ı çalıştırır" diyor; `start.vbs` aslında doğrudan `pythonw.exe` çalıştırıyor. Startup klasöründe de kısayol değil, dosyanın birebir kopyası var (`cmp` ile aynı çıktı). İzlenen `scripts/start.bat` ise farklı davranıyor (`python -u`, küçültülmüş konsol).
  - `CLAUDE.md` "Tray Menusu" düz liste gösteriyor. Kodda iki alt menü var: `🎤 Toplantı` ve `⚙ Ayarlar` (`dictation.py:636-673`). README'deki menüde `🎥 Meet Dictation...` hiç yok.
  - README canlı transkript için "1.5sn sessizlik = paragraf sonu" diyor; kodda `LIVE_SILENCE_DURATION = 0.8` (`:236`) ve aynı README'nin tablosu da 0.8 yazıyor.
  - `G:\Drive'ım\Meet Recordings\RawRecords\` yolu şu dört yerde geçiyor: `CLAUDE.md` Meet bölümü, `TODO.md:46`, `CHANGELOG.md:63`, kod yorumu `dictation.py:2125`. Klasör 12 Haziran'da birleştirildi ve artık yok (`index.md` tarihçe notu; `ls` bulamadı).
  - `index.md`, `VoiceDictation/` klasöründe "LIVE" dosyası olduğunu söylüyor. LIVE dosyası aslında temp klasörüne yazılıyor (`:1827`).
  - README'ye göre loglar "günlük rotate" ediliyor. `backupCount=0` olduğu için hiçbiri silinmiyor (`:132`); 157 dosya birikmiş.
- **Kurulum belgesi bağımlılıkları eksik veriyor.** `requirements.txt` yalnız 5 paket listeliyor.
  - Tray için gereken `pystray` + `Pillow` (`:579`) ve menü çubuğu için gereken `rumps` (`:450`) listede yok.
  - `setup.sh` yalnız `mlx-whisper` ekliyor.
  - Windows venv'e bu paketler elle kurulmuş. MacBook'ta temiz kurulum menü çubuğunda hata verir.
- **Hiçbir belgede yer almayan yerel dosyalar:**
  - `.env` (HF token, `:98`)
  - `.local/file-queue` ve `VOICEDICTATION_QUEUE_DIR` (`file_queue.py:32`). Bu kuyruk iFonzo WhatsApp hattının girdisi, yani başka projeye bağımlılık da belgelenmemiş.
  - `models/` (85 MB; yalnız kapalı diarize yolu kullanıyor)
  - HF önbelleği. Önbellek başka projelerle ortak: iFonzo ses aracı "bağımsız large-v3" kullanıyor, 15 Eylül'de değişen Systran large-v3 büyük olasılıkla onun.
- **Belgeler birbirinin işini yapıyor.**
  - `CHANGELOG.md:39-43` açık iş tutuyor (kalibrasyon); bu işler `TODO.md`'de yok.
  - `TODO.md` 23 Mayıs'tan beri güncellenmemiş.
  - `CHANGELOG`'da 12 Haziran Drive birleşmesi ile 14-15 Eylül commit'leri eksik.
  - `CLAUDE.md` sonunda bir tarihçe paragrafı var.
- **Gürültü var.**
  - Kökte Mart tarihli `dictation.log`, `__pycache__/` ve `.playwright-mcp/` duruyor.
  - İzlenen dosyaların 1509/1534'ü BMAD dosyası, ama `_bmad-output/` hiç oluşmamış. `CLAUDE.md` §2 kullanılmayan bir süreci anlatıyor.
- **Adlar karışık.** `RawRecords` PascalCase. Transkript klasörü `VoiceDictation/`, yani proje adıyla aynı. `calibration`, `docs`, `logs` küçük harf İngilizce. `CLAUDE.md` Türkçe karakterli yolların PowerShell ↔ argparse arasında sorun çıkardığını kendisi yazıyor (iPhone bölümü).

## Öneri

**Belge seti.** Her belgenin tek bir görevi olsun, her bilgi tek bir yerde dursun.

| Belge | Tek cümlelik görevi |
|---|---|
| `README.md` | İnsan girişi: ne yapar, hızlı kurulum, kullanım, **Yerel dosyalar** tablosu ve belge haritası. |
| `CLAUDE.md` (≤80 satır) | Ajanın her oturumda bilmesi gereken kurallar ve değişmezler. |
| `docs/nasil-calisir.md` | Mod akışları, tray menüsü, dosya ve iPhone akışları, halüsinasyon katmanları. `CLAUDE.md` §1'den taşınır ve koda göre düzeltilir. |
| `docs/kurulum.md` | Win/Mac kurulumu, otomatik başlatma, Mac'in 4 izni. `auto-start.md` ve README'deki kopyaların yerini alır. |
| `docs/TODO.md` | Yalnız açık işler; Mac doğrulama listesinin tek kopyası burada. |
| `docs/CHANGELOG.md` | Tamamlanan işler, en yenisi üstte. Tek dosya olsun: ayda bir kayıt düşüyor, iFonzo'daki gibi günlük dosyalara gerek yok. |
| `docs/kalibrasyon/` | Bugünkü `calibration/` (README ve okuma metni). |
| `docs/arsiv/` | Eski talimat kopyaları ve biten analiz klasörleri. |

- **`CLAUDE.md`'de kalacaklar:**
  - Commit onayı ve branch politikası
  - Mac hatırlatması (tek satır ve TODO linki)
  - "Kullanım değişmez" listesi: hotkey, tray, wake word, `--transcribe`
  - Veri gizliliği: transkript, ses ve log içerikleri okunmaz
  - Mimarinin 4 satırlık özeti
  - Belge bakım kuralı (aşağıda)
  - Belge haritası linki
- **`CLAUDE.md`'den çıkacaklar:** MCP Tool Map (global kuralın tekrarı), BMAD süreci (en fazla tek satır kalır), Teknoloji Stack, akış anlatımları, tarihçe paragrafı.
- **Yerel dosyalar tablosu:** yalnız `README.md`'de dursun. Repo public olduğu için yollar göreli ya da `~` ile yazılsın.

| Yol | Ne | Nasıl yeniden oluşur | Mac farkı |
|---|---|---|---|
| `venv/` | Python ortamı | `scripts/setup.*` | `venv/bin/` |
| `~/.cache/huggingface/hub/` | Whisper turbo (paylaşımlı önbellek, başka modeller silinmez) | İlk açılışta iner | `mlx-community/whisper-turbo` |
| `models/` | speechbrain (kapalı diarize yolu) | İlk diarize'da iner | Aynı |
| `logs/` | `dictation.log` (günlük, silinmez) ve `dictation.pid` | Kendiliğinden | Aynı |
| `.env` | HF token (yalnız diarize) | Elle girilir | Aynı |
| `veri/gelen/` | Yiğit'in elle bıraktığı dosyalar | Yok, yedek şart | Aynı |
| `veri/ses/`, `veri/transkript/` | Kalıcı çıktılar | Yok, yedek şart | Aynı |
| `.local/file-queue/` | Dış istemci kuyruğu (iFonzo) | Kendiliğinden | Aynı |
| Sistem temp `voicedictation_live/` | LIVE.md ve geçici WAV | Kendiliğinden, sonra silinir | `$TMPDIR` |
| Başlangıç kaydı | Win: `shell:startup\start.vbs` kopyası, içinde sabit repo yolu var | `docs/kurulum.md` | Login Items → `scripts/VoiceDictation.app` |

- **Hedef ağaç:**

```text
VoiceDictation/
├── README.md  CLAUDE.md  LICENSE  requirements.txt
├── dictation.py  file_queue.py
├── docs/        nasil-calisir.md · kurulum.md · TODO.md · CHANGELOG.md · kalibrasyon/ · arsiv/
├── scripts/     setup.* · start.* · VoiceDictation.app   (ad değişmez: Mac izinleri .app yoluna bağlı)
├── tests/
└── git dışı:  veri/{gelen,ses,transkript}/ · venv/ · models/ · logs/ · .local/ · .env
```

- **Adlandırma kuralı:** Yiğit'in elle dokunduğu klasörler Türkçe olsun: `veri/gelen`, `veri/ses`, `veri/transkript`. Araçların beklediği klasörler İngilizce kalsın: `docs`, `tests`, `logs`, `venv`, `models`, `scripts`. Her ikisinde de küçük harf, ASCII ve tek kelime kullanılsın; PascalCase olmasın.
  - `veri/` görünür bir klasör olmalı. Mac Finder nokta ile başlayan klasörleri gizlediği için `gelen/` `.local/` altına konmamalı.
  - Belge adları: `README`, `CLAUDE`, `TODO` ve `CHANGELOG` büyük harf kalsın; diğerleri küçük harf, Türkçe ve kebab-case olsun.
- **Belge bakım kuralı:** Yol, klasör, menü ya da CLI değiştiren her commit, **aynı commit içinde** README "Yerel dosyalar" tablosunu ve `docs/nasil-calisir.md`'yi günceller. Kodda yollar tek bir blokta durur; tablo o bloğun satır satır aynasıdır.
  - Teslim öncesi kontrol: `grep -rn "Drive'ım\|Meet Recordings\|VoiceDictation_Lectures\|RawRecords" README.md CLAUDE.md docs/*.md dictation.py` boş dönmeli (tarihçe için `docs/arsiv` ve `CHANGELOG` hariç).

## Riskler / Açık sorular

- `Records/RawRecords/` içindeki iki Sonar mp4'ü, Sonar'ın `index.md`'deki kaynak referansı. Bu dosyalar repoya taşınırsa Sonar'ın kaynak yolu kırılır. Bunlar Drive'da mı kalsın, repoya mı gelsin?
- Taşıma bitince Drive'daki `Records/` ve `index.md` ne olsun: silinsin mi, yoksa "taşındı → repo README'si" notuyla mı kalsın?
- `veri/gelen/`'deki dosya işlendikten sonra ne olsun? `--transcribe` bugün dosyayı taşıyor, Meet akışı yerinde bırakıyor. Bu iki farklı davranış korunsun mu, yoksa `gelen/` için tek bir kural mı olsun?
- `veri/ses/` yaklaşık 1 GB ve büyüyecek. rclone filtresi bu klasörü yedeğe alsın mı? MacBook'ta yedek düzeni ne olacak?
- MacBook'ta repo aynı yolda mı duracak? `.app` içine repo yolu derlenmiş (`auto-start.md` tarifi `/full/path/to/repo` gömüyor); yol farklıysa `.app` yeniden derlenmeli ve 4 izin yeniden verilmeli.
- Eksik bağımlılıklar (`pystray`, `Pillow`, `rumps`) uygulama paketinde `requirements.txt`'ye mi eklensin? Yoksa belge yalnız "elle kur" mu desin? Ben ekleme yönünde öneriyorum.
- BMAD (1509 izlenen dosya, hiç çıktı üretilmemiş) repoda kalsın mı?
- `logs/` sınırsız birikiyor. Belgeye bir saklama süresi yazılsın mı?
