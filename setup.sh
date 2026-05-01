#!/usr/bin/env bash
# Fedora compatibility setup for ~/dev apps.
# Enables RPM Fusion Free, installs all app dependencies,
# installs required fonts, and patches known Fedora incompatibilities.
#
# Usage: sudo bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/lib/common.sh"

# ── Guards ────────────────────────────────────────────────────────────────────

[[ $EUID -eq 0 ]] || err "Run with sudo: sudo bash setup.sh"

if [[ ! -f /etc/os-release ]]; then
    err "/etc/os-release not found — cannot detect OS."
fi
source /etc/os-release
[[ "${ID:-}" == "fedora" ]] || err "This script is for Fedora only (detected: ${ID:-unknown})."
info "Fedora ${VERSION_ID:-?} detected."

# Resolve the real user's home directory (SUDO_USER is set when using sudo).
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
DEV_DIR="${DEV_DIR:-$REAL_HOME/dev}"
info "Dev directory: $DEV_DIR"

# ── RPM Fusion Free ───────────────────────────────────────────────────────────

section "RPM Fusion Free"
source "$SCRIPT_DIR/lib/rpmfusion.sh"
enable_rpmfusion_free

# ── Dependency installation ───────────────────────────────────────────────────

pkg_installed() { rpm -q "$1" &>/dev/null; }

install_pkgs() {
    local -a missing=()
    for p in "$@"; do
        pkg_installed "$p" || missing+=("$p")
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        info "Installing: ${missing[*]}"
        dnf install -y "${missing[@]}"
    else
        ok "All packages in this group already installed."
    fi
}

# ── Standard Fedora packages ──────────────────────────────────────────────────

section "Standard packages"

install_pkgs \
    python3 \
    python3-gobject \
    python3-tkinter \
    python3-pillow \
    python3-markdown \
    python3-pygments \
    python3-qt5 \
    python3-qt5-multimedia \
    gtk3 \
    gtk4 \
    libadwaita \
    webkit2gtk4.1 \
    gtksourceview4 \
    qt5-qtmultimedia \
    gstreamer1-plugins-good \
    udisks2 \
    parted \
    dosfstools \
    exfatprogs \
    mat2 \
    perl-Image-ExifTool \
    yt-dlp \
    dejavu-sans-fonts \
    clamav \
    clamav-update \
    newsboat \
    sqlite \
    zip \
    unzip \
    curl \
    zenity

# ── RPM Fusion Free packages ──────────────────────────────────────────────────
# ffmpeg, gstreamer1-libav, and ntfs-3g are not in Fedora's default repos.

section "RPM Fusion Free packages"

install_pkgs \
    ffmpeg \
    gstreamer1-libav \
    ntfs-3g

# ── Font cache ────────────────────────────────────────────────────────────────

section "Font cache"
fc-cache -f
ok "Font cache updated."

# ── Patch: fuetem-imager.py watermark font path ───────────────────────────────
# The app tries Arch and Debian font paths and falls back to a tiny default
# font. On Fedora, DejaVu fonts live in /usr/share/fonts/dejavu-sans-fonts/.

section "Patching fuetem-imager.py watermark font"

FUETEM_IMAGER="$DEV_DIR/fuetem-imager/fuetem-imager.py"

if [[ ! -f "$FUETEM_IMAGER" ]]; then
    warn "fuetem-imager.py not found at $FUETEM_IMAGER — skipping."
else
    python3 - "$FUETEM_IMAGER" <<'PYEOF'
import sys

path = sys.argv[1]
with open(path, 'r') as f:
    content = f.read()

FEDORA_FONT = '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf'
MARKER = FEDORA_FONT

if MARKER in content:
    print('Already patched — skipping.')
    sys.exit(0)

OLD = '                font = ImageFont.load_default()'
NEW = (
    '                try:\n'
    '                    font = ImageFont.truetype(\n'
    "                        '" + FEDORA_FONT + "', font_size)\n"
    '                except Exception:\n'
    '                    font = ImageFont.load_default()'
)

if OLD in content:
    with open(path, 'w') as f:
        f.write(content.replace(OLD, NEW, 1))
    print('Patched successfully.')
else:
    print('WARNING: Expected pattern not found — check fuetem-imager.py indentation manually.')
PYEOF
    ok "fuetem-imager.py font patch done."
fi

# ── Fix: runclam.sh ClamAV user ───────────────────────────────────────────────
# Fedora uses 'clamupdate' as the ClamAV system user, not 'clamav'.

section "Fixing runclam.sh"

RUNCLAM="$DEV_DIR/neils-scripts/runclam.sh"

if [[ ! -f "$RUNCLAM" ]]; then
    warn "runclam.sh not found at $RUNCLAM — skipping."
else
    cp "$RUNCLAM" "${RUNCLAM}.bak"
    cp "$SCRIPT_DIR/fixes/runclam.sh" "$RUNCLAM"
    ok "runclam.sh replaced (backup saved as runclam.sh.bak)."
fi

# ── Done ──────────────────────────────────────────────────────────────────────

section "Setup complete"
ok "All Fedora compatibility fixes applied."
info "You can now run each app's own install.sh to deploy them."
