#!/bin/bash
cd "$(dirname "$0")"
nohup venv/bin/python -u dictation.py > /dev/null 2>&1 &
echo "Voice Dictation baslatildi (PID: $!)"
