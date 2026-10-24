@echo off
cd /d "%~dp0\..\.."
start /min "Voice Dictation" cmd /c ".local\venv\Scripts\python -u -X pycache_prefix=.local/__pycache__ -m dev.dictation"
