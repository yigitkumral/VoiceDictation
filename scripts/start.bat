@echo off
cd /d "%~dp0\.."
start /min "Voice Dictation" cmd /c "venv\Scripts\python -u dictation.py"
