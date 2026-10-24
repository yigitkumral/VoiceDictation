-- Uretilen uygulama repo/.local/VoiceDictation.app konumunda durur.
set appPath to POSIX path of (path to me)
do shell script "cd \"$(dirname " & quoted form of appPath & ")/..\" && mkdir -p .local/logs && nohup .local/venv/bin/python -u -X pycache_prefix=.local/__pycache__ -m dev.dictation > .local/logs/applet.log 2>&1 &"
