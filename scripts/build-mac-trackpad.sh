#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
test "$(uname -s)" = Darwin || { echo "macOS required" >&2; exit 1; }
DEST="$PWD/.local/trackpad"
mkdir -p "$DEST"
xcrun clang -std=c11 -Wall -Wextra dev/mac-trackpad/test_gesture.c -o "$DEST/test-gesture"
"$DEST/test-gesture"
# Yeni inode'a derle: calisan daemon'in modulu yerinde degistirilmez.
xcrun clang -dynamiclib -std=c11 -Wall -Wextra -Wno-unused-parameter \
    -framework CoreFoundation -framework ApplicationServices dev/mac-trackpad/trackpad.c \
    -o "$DEST/libvdtrackpad.new.dylib"
codesign --force --sign - "$DEST/libvdtrackpad.new.dylib"
mv "$DEST/libvdtrackpad.new.dylib" "$DEST/libvdtrackpad.dylib"
echo "Hazir: $DEST/libvdtrackpad.dylib (VoiceDictation yeniden acilinca yuklenir)"
