# Paige karşılaştırması · 16 Eylül 2026

**Sonuç: Kısmen — Paige’in raporu belge bakımında yararlı ayrıntılar getiriyor; bunların personadan kaynaklandığı veya genel kaliteyi yükselttiği bu karşılaştırmayla gösterilemiyor.**

**Ölçüm:** Her rapordan beş somut iddia kaynakta kontrol edildi; bu amaçlı örneklem, raporların toplam hata oranı değildir. Benzersizlik, diğer dört raporda bulunmayan sorun kümelerinin aşağıda sayılan **alt sınırıdır**; öneriler ve doğrulanmamış özel veri iddiaları sayılmadı. Kelime sayımı boşluk ayrımlıdır; sayfa düzeni belirtilmediğinden uzunluk yaklaşık ölçüttür.

| Rapor (`sonuc-*.md`) | Doğru / hatalı | Benzersiz ≥ | Kararlılık | Sayfa disiplini: satır / kelime |
|---|---:|---:|---|---|
| techwriter (Paige) | 4 / 1 | 4 | Yüksek; sorularda geri açıyor | Zayıf: 109 / 1304 |
| yapi | 5 / 0 | 2 | Yüksek; BMAD kararı brife uygun | Zayıf: 78 / 1002 |
| yol | 4 / 1 | 1 | Yüksek; ek ayar öneriyor | Zayıf: 80 / 1133 |
| ortam | 5 / 0 | 2 | Yüksek; somut kurulum çözümü | Zayıf: 73 / 1023 |
| astra | 5 / 0 | 1 | Yüksek; en sade yol çözümü | En yakın, yine yoğun: 42 / 628 |

**Kanıt — beşer iddianın denetimi** (kaynak yolları repo köküne göre):

- **`sonuc-techwriter.md:14,15,20,25` doğru:** README’nin WAV yazılmadığı, iki MD üretildiği ve 1,5 saniye sessizlik anlatımları kodla çelişiyor (`README.md:134,164,137` ↔ `dictation.py:1928,1632,236`); GUI paketleri eksik (`requirements.txt:1–5` ↔ `dictation.py:450,579–580`). **`:75` hatalı:** `.env` “HF token, yalnız diarize” ile sınırlı değil; genel yükleyici editör ayarını da besler (`dictation.py:96–116,1666`), token yardımcısının çağıranı yok (`:119`).
- **`sonuc-yapi.md:5,15,22,26,34` doğru:** `git ls-files` 1534 toplam, 1147 `_bmad`, 362 skill dosyası verdi; VBS/BAT çelişkisi `docs/auto-start.md:9` ↔ `start.vbs:3`; kuyruk izlenmiyor ve ana kodda bağlantısı yok; `.codex/config.toml:4–5` izlenen Windows yolları taşıyor; `git check-ignore -v` genel `settings.json` kuralını doğruladı (`.gitignore:28`).
- **`sonuc-yol.md:10,18,22,27` doğru:** PID, ses taşıma, kuyruk kökü/bağlantısızlığı ve ad çakışması davranışları `dictation.py:50,1625,1634,1928,1944,2208,2237` ve `file_queue.py:31–32` ile örtüşüyor; yazıcılar `dictation.py:1106,1277` dosyayı yeniden açıyor. **`:11` hatalı:** `.env` için “tek tüketici `_get_hf_token`” denemez; yukarıdaki editör yolu karşı örnek.
- **`sonuc-ortam.md:5,6,11,13,24` doğru:** Eksik GUI paketleri; venv Python 3.14.2 (`venv/pyvenv.cfg:3`); model kopyalama stratejisi (`dictation.py:1340`); tam metin loglama (`:3198,3262`); `_get_hf_token` çağrısının bulunmaması. Sonuncusu, raporun daha geniş “token gereksiz” yorumunu doğrulamaz.
- **`sonuc-astra.md:6–8` içinden beş doğrulama:** sınırsız log (`dictation.py:132`), başlangıç belgesi çelişkisi, eksik GUI paketleri, iki skill ağacının `_bmad` yoluna bağımlılığı (`.claude/skills/bmad-dev/SKILL.md:9`, `.agents/skills/bmad-dev/SKILL.md:9`), yazılmamış kalibrasyon komutu (`calibration/README.md:21`; ana kodda bayrak yok). Startup ve repo VBS dosyalarının hash’leri eşit.

**Farkın kaynağı ve öneri:**

- Paige’in benzersiz dört kümesi eski WAV anlatımı, çift MD anlatımı, menü hiyerarşisi ve sessizlik eşiği (`:14–20`). Diğerlerinin özgün katkıları: yapıdaki yerel exclude ve BMAD güncelleme tarihi (`sonuc-yapi.md:25,39`); POSIX’te göreli kalan Drive yolu (`sonuc-yol.md:25`, yazılabilir çalışma dizini koşuluyla); Python sürümü ve metin loglama (`sonuc-ortam.md:6,13`); iki skill ağacının sabit çağrı yolları (`sonuc-astra.md:8`).
- Paige’in belge görevleri tablosu ve aynı commit’te belge güncelleme kuralı uygulanabilir (`:47–56,97`). Bunlar personanın açıklık vaadiyle uyumlu (`_bmad/bmm/agents/tech-writer/tech-writer.md:50–52`), fakat **odak brifinde zaten istenmiş** (`gorev-techwriter.md:7,11–15`). Kurulum/başlangıçta Paige daha doğru değil; ortam platform koşullu bağımlılık ve göreli başlatıcı önerisiyle daha somut (`sonuc-ortam.md:43–48`). Tablo/liste/kanıt alışkanlığı bütün raporlarda var; Paige’in uzunluğu kısalık vaadini karşılamıyor.
- Paige’in Sonar bağımlılığı ve Mac devri soruları isabetli; dosya davranışını yeniden seçtirmesi (`:104`) ortak brifin kullanım değişmez kararını açıyor. Yolun ek env ayarı (`:43`) ve Astra’nın ayarsız çözümü (`:31`) karşılaştırıldığında personasız da sade, derin analiz mümkün; farklı model nedeniyle Astra kontrol grubu değildir.
- **Persona zorunlu olmasın:** belge düzenleme ve kullanıcıya devir işlerinde isteğe bağlı kullanılsın. Etkisini ölçmek için aynı odak brifini persona açık/kapalı, aynı model/ayar ve kesin kelime sınırıyla tekrarlayıp kör değerlendirin. Mevcut tekil, farklı brifli çıktılar nedensellik göstermez. Özel veri açılmadı; `sonuc-yol.md:30` içindeki transkript alanı sayımı salt metadata sınırını aştığından yeniden doğrulanmadı.
