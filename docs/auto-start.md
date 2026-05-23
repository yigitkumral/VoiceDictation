# Auto-Start — VoiceDictation

Bilgisayar acilisinda / login'de VoiceDictation'in otomatik baslamasi icin platform-ozel kurulum tarifleri. **Bir kez yapilir, sonra dokunulmaz.** Kod her zaman repo'daki guncel `dictation.py`'dan calisir; `git pull` veya dosya duzenleme sonrasi extra adim gerekmez — bir sonraki acilista yeni kod devreye girer.

---

## Windows Auto-Start (Bilgisayar Acilisinda Otomatik Baslatma)

**Mekanizma:** Startup klasorune VBScript koyulur, VBScript konsolsuz olarak `start.bat`'i calistirir.

**Dosyalar:**
- `start.bat` — repo kokunde, `venv/Scripts/python.exe dictation.py` calistirir
- `start.vbs` — repo kokunde, `start.bat`'i konsolsuz (gizli pencere) calistirir
- Windows Startup klasoru kisayolu: `shell:startup` → `start.vbs` kisayolu

**Guncelleme Akisi:**
- `dictation.py` degistiginde startup kisayolu guncellenmez — zaten repo'dan calistirilir
- Tek yapilmasi gereken: `git pull` veya kodu duzenlemek
- Bir sonraki bilgisayar acilisinda yeni kod otomatik devreye girer

**Kurulum Adimlari (bir kez yapilir):**
1. `start.bat` ve `start.vbs` dosyalari repo kokunde olusturulur
2. `Win + R` → `shell:startup` → VBScript'e kisayol koyulur
3. Tamamdir — bir daha dokunulmaz

---

## macOS Auto-Start (Login'de Otomatik Baslatma)

**Mekanizma:** Login Items -> `scripts/VoiceDictation.app` (osacompile uretilen AppleScript .app).
.app `do shell script` ile `venv/bin/python -u dictation.py` calistirir.

> **NEDEN AppleScript .app:** macOS Tahoe Desktop'a TCC kisitlamasi koyuyor.
> - LaunchAgent: mikrofon TCC dialog'u arka planda gosterilemiyor, hang oluyor
> - Login Items + start.sh: TextEdit ile aciliyor, execute olmuyor
> - Login Items + ad-hoc imzali shell-script-app: TCC sessizce reddediyor (`PermissionError`)
> - **Login Items + AppleScript .app:** `Automation` TCC kategorisinde, calisir ✅

**Dosyalar:**
- `scripts/VoiceDictation.app/` — osacompile uretilen .app bundle
  - `Contents/Resources/Scripts/main.scpt` — `do shell script "cd ... && nohup ... &"`
  - `Contents/Info.plist` — `LSUIElement=true` (dock'ta gorunmez)
- `scripts/start.sh` — manuel baslatma icin (Login Items'ta kullanilmaz)

**Guncelleme Akisi:**
- `dictation.py` degistiginde .app guncellenmez — zaten repo'dan calistirilir
- Tek yapilmasi gereken: `git pull` veya kodu duzenlemek
- Bir sonraki login'de yeni kod otomatik devreye girer

**Kurulum Adimlari (bir kez yapilir):**
1. System Settings -> General -> Login Items & Extensions
2. "Open at Login" altinda **+** -> `Cmd+Shift+G` -> `scripts/VoiceDictation.app` yolunu yapistir
3. Ilk acilista **mikrofon** + **otomasyon** izinleri istenir → "Izin Ver"
4. Privacy & Security panellerinde manuel toggle:
   - **Input Monitoring** → `applet` entry'sini AC (Caps Lock hotkey icin)
   - **Accessibility** → `applet` entry'sini AC (Cmd+V + Enter gonderme icin)
5. Dictation'i bir kez yeniden baslat (izin degisikligi icin)
6. Tamamdir — bir daha dokunulmaz

**ZORUNLU 4 IZIN:**
| Izin | Eksikse ne bozulur |
|------|-------------------|
| Mikrofon | Hicbir kayit yapilamaz |
| Otomasyon | .app launcher hata, dictation baslamaz |
| Input Monitoring | Caps Lock algilanmaz (sadece wake word calisir) |
| Accessibility | Metin clipboard'da kalir, paste etmez |

> Stale entry'ler: macOS eski .app denemelerinden TCC'de "VoiceDictation" gibi entry'ler
> birakabilir. **−** butonuyla silinebilir. Aktif olan: `applet`.

**.app yeniden olusturulmasi gerekirse** (osacompile + codesign):
```bash
osacompile -o scripts/VoiceDictation.app <(echo 'do shell script "cd '\''/full/path/to/repo'\'' && nohup venv/bin/python -u dictation.py > /dev/null 2>&1 &"')
# LSUIElement=true ekle Info.plist'e (dock gizleme)
codesign --sign - --force --deep scripts/VoiceDictation.app
```
