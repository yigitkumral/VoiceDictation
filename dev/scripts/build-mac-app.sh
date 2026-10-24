#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
test "$(uname -s)" = Darwin || { echo "macOS required" >&2; exit 1; }
DEST="$PWD/.local/VoiceDictation.app"
if [ -e "$DEST" ]; then
    echo "Mevcut uygulama korunuyor: $DEST. Gecis icin docs/kurulum.md belgesine bakin." >&2
    exit 1
fi
mkdir -p .local/logs
osacompile -o "$DEST" dev/scripts/VoiceDictation.applescript
PLIST="$DEST/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.voicedictation.launcher" "$PLIST" || \
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.voicedictation.launcher" "$PLIST"
codesign --force --sign - "$DEST"
echo "Hazir: $DEST. Login Items ve macOS izinlerini bu uygulama icin ayarlayin."
