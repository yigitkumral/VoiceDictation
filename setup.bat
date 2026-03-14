@echo off
echo === Voice Dictation Setup (Windows) ===
echo.

if not exist venv (
    echo [1/3] venv olusturuluyor...
    python -m venv venv
) else (
    echo [1/3] venv zaten var, atlaniyor.
)

echo [2/4] Bagimliliklar kuruluyor...
venv\Scripts\pip install -r requirements.txt

echo [3/4] CUDA kutuphaneleri kuruluyor (GPU destegi)...
venv\Scripts\pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

echo.
echo [4/4] Kurulum tamamlandi!
echo.
echo Calistirmak icin:
echo     venv\Scripts\python dictation.py
echo.
pause
