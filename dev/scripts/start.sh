#!/bin/bash
cd "$(dirname "$0")/../.."
nohup .local/venv/bin/python -u -X pycache_prefix=.local/__pycache__ -m dev.dictation > /dev/null 2>&1 &
echo "Voice Dictation baslatildi (PID: $!)"
