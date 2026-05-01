#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lipcord"
BIN_DIR="$HOME/.local/bin"

echo "=== LipCord Installer ==="
echo

# Install tkinter if needed
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "[*] Installing tkinter (required for the GUI)..."
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tk
    elif command -v apt &>/dev/null; then
        sudo apt install -y python3-tk
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-tkinter
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y python3-tk
    else
        echo "[!] Could not detect package manager. Please install tkinter manually."
        exit 1
    fi
    echo "[+] Installed tkinter"
fi

# Install files
mkdir -p "$BIN_DIR"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"

cp "$SCRIPT_DIR/lipcord" "$BIN_DIR/lipcord"
chmod +x "$BIN_DIR/lipcord"
echo "[+] Installed lipcord (GUI) to $BIN_DIR/lipcord"

cp "$SCRIPT_DIR/lipcord-daemon" "$BIN_DIR/lipcord-daemon"
chmod +x "$BIN_DIR/lipcord-daemon"
echo "[+] Installed lipcord-daemon to $BIN_DIR/lipcord-daemon"

# Install default config if none exists
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config" ]; then
    cat > "$CONFIG_DIR/config" << 'EOF'
# LipCord Configuration

# Lock the session when LipCord USB is removed (yes/no)
LOCK=yes

# Suspend the system when LipCord USB is removed (yes/no)
SUSPEND=yes

# Polling interval in seconds
POLL_INTERVAL=1
EOF
    echo "[+] Created default config at $CONFIG_DIR/config"
else
    echo "[=] Config already exists at $CONFIG_DIR/config (kept existing)"
fi

# Install icons
mkdir -p "$ICON_DIR/scalable/apps" "$ICON_DIR/128x128/apps" "$ICON_DIR/256x256/apps"
cp "$SCRIPT_DIR/icons/lipcord.svg" "$ICON_DIR/scalable/apps/lipcord.svg"
cp "$SCRIPT_DIR/icons/lipcord-128.png" "$ICON_DIR/128x128/apps/lipcord.png"
cp "$SCRIPT_DIR/icons/lipcord-256.png" "$ICON_DIR/256x256/apps/lipcord.png"
gtk-update-icon-cache "$ICON_DIR" 2>/dev/null || true
echo "[+] Installed icons"

# Install desktop entry
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/lipcord.desktop" << EOF
[Desktop Entry]
Name=LipCord
Comment=Physical security failsafe - USB ripcord monitor
Exec=$BIN_DIR/lipcord
Icon=lipcord
Type=Application
Categories=Utility;Security;
Keywords=security;usb;lock;
EOF
echo "[+] Installed desktop entry"

echo
echo "=== LipCord installed ==="
echo "Run 'lipcord' or find LipCord in your app launcher."
echo "Edit $CONFIG_DIR/config to customize behavior."
