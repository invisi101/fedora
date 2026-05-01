#!/usr/bin/env bash
set -euo pipefail

RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
PIDFILE="$RUNTIME_DIR/lipcord.pid"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

echo "=== LipCord Uninstaller ==="
echo

# Stop daemon if running
if [ -f "$PIDFILE" ]; then
    pid=$(cat "$PIDFILE" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "[+] Stopped running daemon"
    fi
    rm -f "$PIDFILE"
fi

# Remove files
rm -f "$BIN_DIR/lipcord" "$BIN_DIR/lipcord-daemon"
echo "[+] Removed lipcord and lipcord-daemon from $BIN_DIR"

rm -f "$DESKTOP_DIR/lipcord.desktop"
echo "[+] Removed desktop entry"

ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
rm -f "$ICON_DIR/scalable/apps/lipcord.svg"
rm -f "$ICON_DIR/128x128/apps/lipcord.png"
rm -f "$ICON_DIR/256x256/apps/lipcord.png"
gtk-update-icon-cache "$ICON_DIR" 2>/dev/null || true
echo "[+] Removed icons"

echo
read -rp "Remove config at ~/.config/lipcord/? [y/N] " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    rm -rf "${XDG_CONFIG_HOME:-$HOME/.config}/lipcord"
    echo "[+] Removed config"
else
    echo "[=] Config kept"
fi

echo
echo "=== LipCord has been uninstalled ==="
