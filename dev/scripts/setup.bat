@echo off
cd /d "%~dp0\..\.."
set "VD_REPO=%CD%"
echo === VoiceDictation Kurulum (Windows) ===
echo.

if not exist .local\venv (
    echo [1/3] venv olusturuluyor...
    python -m venv .local/venv
) else (
    echo [1/3] venv zaten var, atlaniyor.
)

echo [2/3] Bagimliliklar kuruluyor - CUDA ve tepsi paketleri dahil...
.local\venv\Scripts\python -m pip install -r dev/requirements.txt
if errorlevel 1 (
    echo HATA: Bagimliliklar kurulamadi.
    pause
    exit /b 1
)

echo [3/3] Baslangic kisayolu yaziliyor: Startup\VoiceDictation.lnk -^> dev\scripts\start.vbs
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $r=$env:VD_REPO; $l=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\VoiceDictation.lnk'; $s=(New-Object -ComObject WScript.Shell).CreateShortcut($l); $s.TargetPath=Join-Path $env:WINDIR 'System32\wscript.exe'; $s.Arguments=[char]34+(Join-Path $r 'dev\scripts\start.vbs')+[char]34; $s.WorkingDirectory=$r; $s.Save(); Write-Host ('      '+$l)"
if errorlevel 1 echo UYARI: Kisayol yazilamadi; dev\scripts\start.vbs icin Startup klasorune elle kisayol ekleyin.
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\start.vbs" (
    echo UYARI: Startup klasorunde eski start.vbs kopyasi var; cift baslatmamak icin elle silin.
)

echo.
echo Kurulum tamamlandi.
echo     Veri:  .local\data\          Log: .local\logs\
echo     Baslat: wscript dev\scripts\start.vbs  (gizli)  veya  dev\scripts\start.bat  (konsollu)
echo.
pause
