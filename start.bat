@echo off
start /min "Voice Dictation" cmd /c "cd /d %~dp0 && venv\Scripts\python -u dictation.py"
