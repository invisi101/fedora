#!/usr/bin/env bash
set -e

# ---------------------------------------------------------------------------
# Dependency check + install
# ---------------------------------------------------------------------------

check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "ERROR: python3 not found. Please install Python 3.10 or newer."
        exit 1
    fi
    ver=$(python3 -c "import sys; print(sys.version_info[:2])")
    major=$(python3 -c "import sys; print(sys.version_info.major)")
    minor=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
        echo "ERROR: Python 3.10+ required (found $major.$minor)."
        exit 1
    fi
}

missing_deps() {
    local missing=()
    python3 -c "import PyQt5" 2>/dev/null            || missing+=("pyqt5")
    python3 -c "from PyQt5.QtMultimedia import QMediaPlayer" 2>/dev/null \
                                                       || missing+=("qt5-multimedia")
    command -v ffmpeg &>/dev/null                      || missing+=("ffmpeg")
    # GStreamer libav backend — needed for format decoding via Qt5Multimedia
    if ! python3 -c "
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QApplication
import sys
app = QApplication.instance() or QApplication(sys.argv)
p = QMediaPlayer()
# A non-empty service name means a backend was found
exit(0 if p.service() else 1)
" 2>/dev/null; then
        missing+=("gst-libav")
    fi
    echo "${missing[@]}"
}

install_deps() {
    local pkgs=("$@")
    [ ${#pkgs[@]} -eq 0 ] && return

    if command -v pacman &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python-pyqt5"
            [qt5-multimedia]="qt5-multimedia"
            [gst-libav]="gst-plugins-good gst-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        echo "Installing: ${to_install[*]}"
        sudo pacman -S --needed --noconfirm "${to_install[@]}"

    elif command -v apt-get &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python3-pyqt5"
            [qt5-multimedia]="python3-pyqt5.qtmultimedia"
            [gst-libav]="gstreamer1.0-plugins-good gstreamer1.0-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        echo "Installing: ${to_install[*]}"
        sudo apt-get install -y "${to_install[@]}"

    elif command -v dnf &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python3-qt5"
            [qt5-multimedia]="qt5-qtmultimedia"
            [gst-libav]="gstreamer1-plugins-good gstreamer1-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        echo "Installing: ${to_install[*]}"
        sudo dnf install -y "${to_install[@]}"

    elif command -v zypper &>/dev/null; then
        declare -A pm_map=(
            [pyqt5]="python3-qt5"
            [qt5-multimedia]="libqt5-qtmultimedia"
            [gst-libav]="gstreamer-plugins-good gstreamer-plugins-libav"
            [ffmpeg]="ffmpeg"
        )
        local to_install=()
        for dep in "${pkgs[@]}"; do
            to_install+=( ${pm_map[$dep]} )
        done
        echo "Installing: ${to_install[*]}"
        sudo zypper install -y "${to_install[@]}"

    else
        echo ""
        echo "Could not detect a supported package manager (pacman/apt/dnf/zypper)."
        echo "Please install the following manually, then re-run this script:"
        for dep in "${pkgs[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

echo "Checking dependencies…"
check_python

if [[ -z "${FEDORA_SETUP:-}" ]]; then
    missing=( $(missing_deps) )

    if [ ${#missing[@]} -gt 0 ]; then
        echo ""
        echo "Missing dependencies: ${missing[*]}"
        read -rp "Install them now? [Y/n] " answer
        answer=${answer:-Y}
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            install_deps "${missing[@]}"
        else
            echo "Aborted. Install the missing dependencies and re-run."
            exit 1
        fi
    else
        echo "All dependencies satisfied."
    fi
fi

# ---------------------------------------------------------------------------
# Install app files
# ---------------------------------------------------------------------------

INSTALL_DIR="$HOME/.local/bin"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
APPS_DIR="$HOME/.local/share/applications"

mkdir -p "$INSTALL_DIR" "$ICONS_DIR" "$APPS_DIR"

cp fuetem_audio.py "$INSTALL_DIR/fuetem-audio"
chmod +x "$INSTALL_DIR/fuetem-audio"

cp icons/fuetem-audio.svg "$ICONS_DIR/"

cat > "$APPS_DIR/fuetem-audio.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Fuetem Audio
Comment=Audio file converter, trimmer, and player
Exec=$INSTALL_DIR/fuetem-audio
Icon=fuetem-audio
Categories=AudioVideo;Audio;
StartupNotify=false
EOF

echo ""
echo "Fuetem Audio installed successfully."
echo "Launch with: fuetem-audio"
