#!/bin/bash
set -e

echo "Uninstalling EmDee Editor..."

sudo rm -f /usr/local/bin/emdee-editor
rm -f "$HOME/.local/share/applications/emdee-editor.desktop"
sudo rm -f /usr/share/icons/hicolor/scalable/apps/emdee-editor.svg
gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true

echo "Done! EmDee Editor has been uninstalled."
echo "Config remains at ~/.config/emdee-editor/ — delete manually if desired."
