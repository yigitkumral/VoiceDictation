@echo off
echo === Voice Dictation Setup (Windows) ===
echo.

if not exist venv (
    echo [1/3] venv olusturuluyor...
    python -m venv venv
) else (
    echo [1/3] venv zaten var, atlaniyor.
)

echo [2/3] Bagimliliklar kuruluyor...
venv\Scripts\pip install -r requirements.txt

echo.
echo [3/3] Kurulum tamamlandi!
echo.
echo Calistirmak icin:
echo     venv\Scripts\python dictation.py
echo.
pause
