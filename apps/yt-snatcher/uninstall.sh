#!/bin/bash
set -euo pipefail

echo "=== YT Snatcher uninstaller ==="

rm -f "$HOME/.local/bin/yt-snatcher"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/yt-snatcher.svg"
rm -f "$HOME/.local/share/applications/yt-snatcher.desktop"

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo "YT Snatcher has been removed."
