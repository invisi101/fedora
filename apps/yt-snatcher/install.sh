#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "=== YT Snatcher installer ==="

# Detect package manager and install dependencies
install_deps() {
    if command -v pacman &>/dev/null; then
        local deps=()
        pacman -Qi yt-dlp &>/dev/null || deps+=(yt-dlp)
        pacman -Qi python-pyqt5 &>/dev/null || deps+=(python-pyqt5)
        if [ ${#deps[@]} -gt 0 ]; then
            echo "Installing (pacman): ${deps[*]}"
            sudo pacman -S --needed --noconfirm "${deps[@]}"
        fi
    elif command -v dnf &>/dev/null; then
        echo "Installing dependencies (dnf)..."
        sudo dnf install -y yt-dlp python3-qt5
    elif command -v apt &>/dev/null; then
        echo "Installing dependencies (apt)..."
        sudo apt update
        sudo apt install -y yt-dlp python3-pyqt5
    else
        echo "WARNING: Could not detect package manager."
        echo "Please install manually: yt-dlp, python3 PyQt5"
        echo "Continuing with file installation..."
    fi
}

echo "Checking dependencies..."
install_deps

# Install script
mkdir -p "$BIN_DIR"
cp "$SCRIPT_DIR/yt_snatcher.py" "$BIN_DIR/yt-snatcher"
chmod +x "$BIN_DIR/yt-snatcher"
echo "Installed yt-snatcher to $BIN_DIR/"

# Install icon
mkdir -p "$ICON_DIR"
cp "$SCRIPT_DIR/icons/yt-snatcher.svg" "$ICON_DIR/yt-snatcher.svg"
echo "Installed icon to $ICON_DIR/"

# Install desktop file (patch Exec to use full path)
mkdir -p "$DESKTOP_DIR"
sed "s|^Exec=yt-snatcher|Exec=$BIN_DIR/yt-snatcher|" "$SCRIPT_DIR/yt-snatcher.desktop" > "$DESKTOP_DIR/yt-snatcher.desktop"
echo "Installed desktop entry to $DESKTOP_DIR/"

# Update desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo ""
echo "=== Done! ==="
echo "You can now launch YT Snatcher from your app menu or run: yt-snatcher"
