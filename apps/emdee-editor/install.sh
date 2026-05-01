#!/bin/bash
set -e

echo "Installing EmDee Editor..."

# Detect distro and install dependencies
install_deps() {
    if command -v pacman &>/dev/null; then
        echo "Detected Arch Linux"
        sudo pacman -S --needed --noconfirm python gtk3 webkit2gtk-4.1 python-gobject python-markdown python-pygments gtksourceview4
    elif command -v apt &>/dev/null; then
        echo "Detected Debian/Ubuntu"
        sudo apt install -y python3 gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-gi python3-markdown python3-pygments gir1.2-gtksource-4
    elif command -v dnf &>/dev/null; then
        echo "Detected Fedora"
        sudo dnf install -y python3 gtk3 webkit2gtk4.1 python3-gobject python3-markdown python3-pygments gtksourceview4
    else
        echo "Could not detect package manager. Please install these manually:"
        echo "  python3, gtk3, webkit2gtk-4.1, python-gobject, python-markdown, pygments, gtksourceview4"
        exit 1
    fi
}

install_deps

# Install the app
sudo install -Dm755 emdee-editor.py /usr/local/bin/emdee-editor
install -Dm644 emdee-editor.desktop "$HOME/.local/share/applications/emdee-editor.desktop"
sudo install -Dm644 emdee-editor.svg /usr/share/icons/hicolor/scalable/apps/emdee-editor.svg
gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true

echo "Done! Launch 'EmDee Editor' from your app launcher or run: emdee-editor"
