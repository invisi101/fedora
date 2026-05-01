#!/usr/bin/env bash
# Fedora setup: enables RPM Fusion Free, installs all system packages,
# and deploys all bundled apps from this repo.
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

# ── App installation ──────────────────────────────────────────────────────────
# run_as_user: subshell in app dir as REAL_USER with HOME set correctly.
#   Used for apps installing to ~/.local (user-space).
# run_as_root: subshell in app dir as root with HOME set to REAL_HOME so
#   desktop entries land in the real user's home, not /root.

run_as_user() {
    local app_dir="$1"
    (cd "$app_dir" && sudo -u "$REAL_USER" HOME="$REAL_HOME" bash install.sh)
}

run_as_root() {
    local app_dir="$1"
    (cd "$app_dir" && HOME="$REAL_HOME" bash install.sh)
}

section "yt-snatcher"
run_as_user "$SCRIPT_DIR/apps/yt-snatcher"

section "pikapika"
run_as_user "$SCRIPT_DIR/apps/pikapika"

section "LipCord"
run_as_user "$SCRIPT_DIR/apps/lipcord"

section "emdee-editor"
run_as_root "$SCRIPT_DIR/apps/emdee-editor"

section "emdee-viewer"
run_as_root "$SCRIPT_DIR/apps/emdee-viewer"

section "fuetem-audio"
run_as_user "$SCRIPT_DIR/apps/fuetem-audio"

section "fuetem-imager"
run_as_root "$SCRIPT_DIR/apps/fuetem-imager"

# ── neils-scripts ─────────────────────────────────────────────────────────────

section "neils-scripts"
SCRIPTS_BIN="$REAL_HOME/.local/bin"
sudo -u "$REAL_USER" mkdir -p "$SCRIPTS_BIN"
install -Dm755 "$SCRIPT_DIR/apps/neils-scripts/runclam.sh" "$SCRIPTS_BIN/runclam"
install -Dm755 "$SCRIPT_DIR/apps/neils-scripts/url-maintenance.sh" "$SCRIPTS_BIN/url-maintenance"
chown "$REAL_USER:$REAL_USER" "$SCRIPTS_BIN/runclam" "$SCRIPTS_BIN/url-maintenance"
ok "Scripts installed to $SCRIPTS_BIN/"

# ── firefox-settings ─────────────────────────────────────────────────────────
# Interactive — must be run separately as yourself after Firefox has been
# opened at least once to create a profile directory.

section "Firefox settings"
warn "Firefox settings require manual setup (interactive profile selection)."
info "Run as yourself (not sudo) after first launching Firefox:"
info "  cd $SCRIPT_DIR/apps/firefox-settings && bash install.sh"

# ── Done ──────────────────────────────────────────────────────────────────────

section "Setup complete"
ok "All apps installed."
info "Log out and back in to refresh PATH and icon caches."
