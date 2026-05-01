#!/usr/bin/env bash
# Fedora setup: enables RPM Fusion Free, installs all system packages,
# deploys all bundled apps, and configures the terminal environment.
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
    zsh \
    kitty \
    fastfetch \
    neovim \
    eza \
    bat \
    fzf \
    zoxide \
    yazi \
    thefuck \
    trash-cli \
    ripgrep \
    multitail \
    mousepad \
    net-tools \
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
for script in runclam.sh url-maintenance.sh pullmygit.sh pushmygit.sh; do
    base="${script%.sh}"
    install -Dm755 "$SCRIPT_DIR/apps/neils-scripts/$script" "$SCRIPTS_BIN/$base"
    chown "$REAL_USER:$REAL_USER" "$SCRIPTS_BIN/$base"
done
ok "Scripts installed to $SCRIPTS_BIN/"

# ── Terminal environment ──────────────────────────────────────────────────────

section "Terminal: unimatrix"
if sudo -u "$REAL_USER" HOME="$REAL_HOME" pip3 install --user --quiet unimatrix 2>/dev/null; then
    ok "unimatrix installed."
else
    warn "unimatrix install failed — skipping (install manually: pip3 install unimatrix --user)."
fi

section "Terminal: Oh My Zsh"
OMZ_DIR="$REAL_HOME/.oh-my-zsh"
if [[ -d "$OMZ_DIR" ]]; then
    ok "Oh My Zsh already installed."
else
    info "Installing Oh My Zsh..."
    sudo -u "$REAL_USER" HOME="$REAL_HOME" \
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
        "" --unattended
    ok "Oh My Zsh installed."
fi

section "Terminal: Powerlevel10k theme"
P10K_DIR="$REAL_HOME/.oh-my-zsh/custom/themes/powerlevel10k"
if [[ -d "$P10K_DIR" ]]; then
    ok "Powerlevel10k already installed."
else
    info "Cloning Powerlevel10k..."
    sudo -u "$REAL_USER" git clone --depth=1 \
        https://github.com/romkatv/powerlevel10k.git "$P10K_DIR"
    ok "Powerlevel10k installed."
fi

section "Terminal: zsh plugins"
ZSH_CUSTOM="$REAL_HOME/.oh-my-zsh/custom/plugins"

AUTOSUG_DIR="$ZSH_CUSTOM/zsh-autosuggestions"
if [[ -d "$AUTOSUG_DIR" ]]; then
    ok "zsh-autosuggestions already installed."
else
    info "Cloning zsh-autosuggestions..."
    sudo -u "$REAL_USER" git clone --depth=1 \
        https://github.com/zsh-users/zsh-autosuggestions.git "$AUTOSUG_DIR"
    ok "zsh-autosuggestions installed."
fi

SYNTHIGH_DIR="$ZSH_CUSTOM/zsh-syntax-highlighting"
if [[ -d "$SYNTHIGH_DIR" ]]; then
    ok "zsh-syntax-highlighting already installed."
else
    info "Cloning zsh-syntax-highlighting..."
    sudo -u "$REAL_USER" git clone --depth=1 \
        https://github.com/zsh-users/zsh-syntax-highlighting.git "$SYNTHIGH_DIR"
    ok "zsh-syntax-highlighting installed."
fi

section "Terminal: JetBrainsMono Nerd Font"
FONT_DIR="$REAL_HOME/.local/share/fonts/JetBrainsMonoNF"
sudo -u "$REAL_USER" mkdir -p "$FONT_DIR"
for ttf in "$SCRIPT_DIR/configs/fonts/"*.ttf; do
    dest="$FONT_DIR/$(basename "$ttf")"
    if [[ ! -f "$dest" ]]; then
        install -Dm644 "$ttf" "$dest"
        chown "$REAL_USER:$REAL_USER" "$dest"
    fi
done
fc-cache -f "$FONT_DIR"
ok "JetBrainsMono Nerd Font installed."

section "Terminal: dotfiles"
# .zshrc — back up existing if present
if [[ -f "$REAL_HOME/.zshrc" && ! -f "$REAL_HOME/.zshrc.prefedora" ]]; then
    cp "$REAL_HOME/.zshrc" "$REAL_HOME/.zshrc.prefedora"
    chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.zshrc.prefedora"
    info "Existing .zshrc backed up as .zshrc.prefedora"
fi
install -Dm644 "$SCRIPT_DIR/configs/zsh/.zshrc" "$REAL_HOME/.zshrc"
install -Dm644 "$SCRIPT_DIR/configs/zsh/.p10k.zsh" "$REAL_HOME/.p10k.zsh"
chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.zshrc" "$REAL_HOME/.p10k.zsh"
ok "zsh dotfiles deployed."

section "Terminal: kitty config"
KITTY_DIR="$REAL_HOME/.config/kitty"
sudo -u "$REAL_USER" mkdir -p "$KITTY_DIR"
for f in "$SCRIPT_DIR/configs/kitty/"*; do
    install -Dm644 "$f" "$KITTY_DIR/$(basename "$f")"
    chown "$REAL_USER:$REAL_USER" "$KITTY_DIR/$(basename "$f")"
done
ok "kitty config deployed."

section "Terminal: set default shell to zsh"
CURRENT_SHELL=$(getent passwd "$REAL_USER" | cut -d: -f7)
if [[ "$CURRENT_SHELL" == "$(command -v zsh)" ]]; then
    ok "zsh is already the default shell."
else
    chsh -s "$(command -v zsh)" "$REAL_USER"
    ok "Default shell set to zsh (takes effect on next login)."
fi

# ── Claude Code ───────────────────────────────────────────────────────────────

section "Claude Code"
if command -v claude &>/dev/null; then
    ok "Claude Code already installed ($(claude --version 2>/dev/null | head -1))."
else
    info "Installing Claude Code..."
    sudo -u "$REAL_USER" HOME="$REAL_HOME" \
        sh -c "$(curl -fsSL https://claude.ai/install.sh)"
    ok "Claude Code installed."
fi

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
