#!/usr/bin/env bash
# Fedora setup: full system configuration for MangoWM + DMS.
# Installs all packages, builds MangoWM/scenefx, deploys all configs.
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

REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
info "Installing for user: $REAL_USER ($REAL_HOME)"

# ── Helpers ───────────────────────────────────────────────────────────────────

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
        ok "All packages already installed."
    fi
}

copr_enable() {
    local repo="$1"
    if dnf copr list --enabled 2>/dev/null | grep -qF "${repo##*/}"; then
        ok "COPR $repo already enabled."
    else
        info "Enabling COPR: $repo"
        dnf copr enable -y "$repo" || warn "COPR $repo failed — continuing."
    fi
}

repo_add() {
    local name="$1" url="$2"
    if dnf repolist --all 2>/dev/null | grep -qi "$name"; then
        ok "Repo $name already present."
    else
        info "Adding repo: $name"
        dnf config-manager addrepo --from-repofile="$url"
    fi
}

# Run a subshell as REAL_USER in a given app directory (user-space installs).
# FEDORA_SETUP=1 tells the app's install.sh to skip its own dep install
# (we install all deps centrally in setup.sh, no inner sudo prompt needed).
run_as_user() {
    local app_dir="$1"
    (cd "$app_dir" && sudo -u "$REAL_USER" HOME="$REAL_HOME" FEDORA_SETUP=1 bash install.sh)
}

# Run a subshell as root in a given app directory with HOME set to real user's home.
run_as_root() {
    local app_dir="$1"
    (cd "$app_dir" && HOME="$REAL_HOME" FEDORA_SETUP=1 bash install.sh)
}

# Deploy a config file, expanding $HOME to REAL_HOME via envsubst.
deploy_config() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    HOME="$REAL_HOME" envsubst '$HOME' < "$src" > "$dest"
    chown "$REAL_USER:$REAL_USER" "$dest"
}

# ── System update ─────────────────────────────────────────────────────────────

section "System update"
dnf -y upgrade --refresh
ok "System up to date."

# ── DNF plugins ───────────────────────────────────────────────────────────────

section "DNF plugins"
install_pkgs dnf-plugins-core dnf5-plugins curl git wget

# ── Repositories ─────────────────────────────────────────────────────────────

section "RPM Fusion Free"
source "$SCRIPT_DIR/lib/rpmfusion.sh"
enable_rpmfusion_free

section "Terra repo"
if ! dnf repolist --all 2>/dev/null | grep -qi "terra"; then
    info "Adding Terra repo..."
    dnf config-manager addrepo \
        --from-repofile=https://github.com/terrapkg/subatomic-repos/raw/main/terra.repo
    dnf install -y terra-release || true
else
    ok "Terra repo already present."
fi

# Pin Terra to lower priority than Fedora's repos (default 99 = highest;
# higher number = lower priority). Keeps Fedora packages winning on
# conflicts so Terra only fills gaps (mangowm, scenefx) rather than
# silently shadowing system packages on dnf upgrade.
for f in /etc/yum.repos.d/terra*.repo; do
    [[ -f "$f" ]] || continue
    if ! grep -q '^priority=' "$f"; then
        sed -i '/^\[/a priority=200' "$f"
        info "Set priority=200 on $(basename "$f")."
    fi
done

section "COPR repos"
copr_enable "avengemedia/dms"
copr_enable "scottames/ghostty"

section "Brave repo"
if ! dnf repolist --all 2>/dev/null | grep -qi "brave-browser"; then
    info "Adding Brave repo..."
    rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.asc
    dnf config-manager addrepo \
        --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
else
    ok "Brave repo already present."
fi

# ── Standard packages ─────────────────────────────────────────────────────────

section "Standard packages"

install_pkgs \
    `# ── Terminal / shell ──────────────────────` \
    zsh fish tmux \
    `# ── Terminal emulators ────────────────────` \
    kitty alacritty foot ghostty \
    `# ── Eye candy ─────────────────────────────` \
    fastfetch btop htop cava cbonsai figlet \
    `# ── File management ───────────────────────` \
    yazi nautilus ncdu fd-find \
    `# ── Editors ───────────────────────────────` \
    nano mousepad \
    `# ── Browsers ──────────────────────────────` \
    firefox torbrowser-launcher brave-browser \
    `# ── Media ─────────────────────────────────` \
    mpv \
    `# ── Bluetooth / power / login manager ─────` \
    bluez power-profiles-daemon sddm \
    `# ── Security ──────────────────────────────` \
    ufw firejail lynis rkhunter gitleaks \
    `# ── Dev tools ─────────────────────────────` \
    git gh jq ImageMagick shellcheck cmake meson \
    `# ── Productivity ──────────────────────────` \
    newsboat transmission-gtk calibre kiwix-desktop gnome-feeds \
    easyeffects rpi-imager \
    `# ── Python ────────────────────────────────` \
    python3 python3-pip pipx \
    python3-gobject python3-tkinter python3-pillow \
    python3-markdown python3-pygments \
    python3-qt5 python3-qt5-multimedia \
    `# ── WM runtime ────────────────────────────` \
    xdg-desktop-portal xdg-desktop-portal-wlr xdg-desktop-portal-gtk \
    polkit polkit-gnome \
    wl-clipboard cliphist \
    grim slurp brightnessctl playerctl pamixer pavucontrol \
    xorg-x11-server-Xwayland \
    fuzzel swayidle swaylock \
    rofi rofimoji hyprpicker wlr-randr satty \
    wireplumber pipewire pipewire-alsa pipewire-jack pipewire-pulse \
    gnome-keyring \
    `# ── Shell tools ───────────────────────────` \
    eza bat fzf zoxide thefuck trash-cli ripgrep multitail \
    `# ── GTK / app dependencies ────────────────` \
    gtk3 gtk4 libadwaita webkit2gtk4.1 gtksourceview4 \
    qt5-qtmultimedia gstreamer1-plugins-good \
    `# ── Disk / filesystem ─────────────────────` \
    udisks2 \
    `# ── Misc ──────────────────────────────────` \
    mat2 perl-Image-ExifTool yt-dlp dejavu-sans-fonts \
    clamav clamav-update sqlite zenity

# ── RPM Fusion packages ───────────────────────────────────────────────────────
# ffmpeg and gstreamer1-libav need RPM Fusion (codec licensing).

section "RPM Fusion packages"
install_pkgs ffmpeg gstreamer1-libav

# ── Graphics runtime ──────────────────────────────────────────────────────────
# Most graphics libs come in via mangowm + xdg-desktop-portal; mesa-dri-drivers
# is the one we want explicit so hardware accel works on first boot.

section "Graphics runtime"
install_pkgs mesa-dri-drivers

# ── Font cache ────────────────────────────────────────────────────────────────

section "Font cache"
fc-cache -f
ok "Font cache updated."

# ── Flatpak ───────────────────────────────────────────────────────────────────

section "Flatpak"
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
ok "Flathub remote configured."

section "Flatpak apps"
for app in com.rafaelmardojai.Blanket io.freetubeapp.FreeTube org.standardnotes.standardnotes; do
    if flatpak list --app | grep -q "$app"; then
        ok "$app already installed."
    else
        info "Installing $app..."
        flatpak install -y flathub "$app"
    fi
done

# Wrapper so binds.conf SUPER+N (-> $HOME/.local/bin/standard-notes) works.
SN_WRAPPER="$REAL_HOME/.local/bin/standard-notes"
sudo -u "$REAL_USER" mkdir -p "$REAL_HOME/.local/bin"
cat > "$SN_WRAPPER" <<'EOF'
#!/bin/sh
exec flatpak run org.standardnotes.standardnotes "$@"
EOF
chmod 755 "$SN_WRAPPER"
chown "$REAL_USER:$REAL_USER" "$SN_WRAPPER"
ok "standard-notes wrapper deployed."

# ── Starship prompt ───────────────────────────────────────────────────────────

section "Starship"
if command -v starship &>/dev/null; then
    ok "Starship already installed."
else
    info "Installing Starship..."
    curl -sS https://starship.rs/install.sh | sh -s -- -y
    ok "Starship installed."
fi

# ── Trufflehog ────────────────────────────────────────────────────────────────

section "Trufflehog"
if command -v trufflehog &>/dev/null; then
    ok "Trufflehog already installed."
else
    info "Installing Trufflehog..."
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
        | sh -s -- -b /usr/local/bin
    ok "Trufflehog installed."
fi

# ── pipx / pip tools ─────────────────────────────────────────────────────────

section "terminaltexteffects (screensaver)"
if sudo -u "$REAL_USER" HOME="$REAL_HOME" pipx list 2>/dev/null | grep -q terminaltexteffects; then
    ok "terminaltexteffects already installed."
else
    info "Installing terminaltexteffects..."
    sudo -u "$REAL_USER" HOME="$REAL_HOME" pipx install terminaltexteffects \
        && ok "terminaltexteffects installed." \
        || warn "terminaltexteffects install failed — install manually: pipx install terminaltexteffects"
fi

section "unimatrix"
if sudo -u "$REAL_USER" HOME="$REAL_HOME" pipx list 2>/dev/null | grep -q unimatrix; then
    ok "unimatrix already installed."
else
    info "Installing unimatrix..."
    sudo -u "$REAL_USER" HOME="$REAL_HOME" pipx install unimatrix \
        && ok "unimatrix installed." \
        || warn "unimatrix install failed — install manually: pipx install unimatrix"
fi

# ── UFW firewall ──────────────────────────────────────────────────────────────

section "UFW firewall"
systemctl stop firewalld 2>/dev/null || true
systemctl disable firewalld 2>/dev/null || true
systemctl enable ufw
if ufw status 2>/dev/null | grep -q "Status: active"; then
    ok "UFW already configured — skipping reset to preserve any custom rules."
else
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow from 192.168.1.0/24
    ufw --force enable
    ufw logging low
    ok "UFW enabled: deny incoming, allow outgoing, allow LAN (192.168.1.0/24)."
fi

# ── MangoWM ───────────────────────────────────────────────────────────────────
# Terra repo ships mangowm built against scenefx 0.4 + wlroots0.19 (parallel-
# installed alongside Fedora's wlroots 0.20). RPM auto-pulls runtime deps.

section "MangoWM"
install_pkgs mangowm

# ── DMS (DankMaterialShell) ───────────────────────────────────────────────────

section "DankMaterialShell"
if command -v dms &>/dev/null; then
    ok "DMS already installed."
else
    info "Installing DMS..."
    if ! dnf install -y dms 2>/dev/null; then
        info "COPR install failed — trying official dankinstall script..."
        sudo -u "$REAL_USER" HOME="$REAL_HOME" \
            sh -c "$(curl -fsSL https://install.danklinux.com)"
    fi
    ok "DMS installed."
fi

# ── MangoWM config ────────────────────────────────────────────────────────────

section "MangoWM config"
MANGO_DIR="$REAL_HOME/.config/mango"
sudo -u "$REAL_USER" mkdir -p "$MANGO_DIR/dms"

deploy_config "$SCRIPT_DIR/configs/mango/config.conf"  "$MANGO_DIR/config.conf"
deploy_config "$SCRIPT_DIR/configs/mango/binds.conf"   "$MANGO_DIR/binds.conf"

# autostart wrapper — uses runtime $HOME, no envsubst needed
install -Dm755 "$SCRIPT_DIR/configs/mango/autostart.sh" "$MANGO_DIR/autostart.sh"
chown "$REAL_USER:$REAL_USER" "$MANGO_DIR/autostart.sh"

# screensaver text — no $HOME expansion needed
install -Dm644 "$SCRIPT_DIR/configs/mango/screensaver.txt" "$MANGO_DIR/screensaver.txt"
chown "$REAL_USER:$REAL_USER" "$MANGO_DIR/screensaver.txt"

# DMS placeholder files — DMS overwrites these on first run
for f in cursor.conf outputs.conf; do
    if [[ ! -f "$MANGO_DIR/dms/$f" ]]; then
        install -Dm644 "$SCRIPT_DIR/configs/mango/dms/$f" "$MANGO_DIR/dms/$f"
        chown "$REAL_USER:$REAL_USER" "$MANGO_DIR/dms/$f"
    fi
done

ok "MangoWM config deployed."

# ── Mango scripts ─────────────────────────────────────────────────────────────

section "MangoWM scripts"
SCRIPTS_SRC="$SCRIPT_DIR/configs/scripts"
BIN_DIR="$REAL_HOME/.local/bin"
sudo -u "$REAL_USER" mkdir -p "$BIN_DIR"

for script in mango-launch-screensaver mango-screensaver screenshot-satty screenshot-full clipboard-rofi; do
    install -Dm755 "$SCRIPTS_SRC/$script" "$BIN_DIR/$script"
    chown "$REAL_USER:$REAL_USER" "$BIN_DIR/$script"
done
ok "MangoWM scripts deployed to $BIN_DIR/"

# ── Terminal: Oh My Zsh ───────────────────────────────────────────────────────

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

# ── Terminal: JetBrainsMono Nerd Font ─────────────────────────────────────────

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

# ── Terminal: dotfiles ────────────────────────────────────────────────────────

section "Terminal: dotfiles"
if [[ -f "$REAL_HOME/.zshrc" && ! -f "$REAL_HOME/.zshrc.prefedora" ]]; then
    cp "$REAL_HOME/.zshrc" "$REAL_HOME/.zshrc.prefedora"
    chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.zshrc.prefedora"
    info "Existing .zshrc backed up as .zshrc.prefedora"
fi
install -Dm644 "$SCRIPT_DIR/configs/zsh/.zshrc"   "$REAL_HOME/.zshrc"
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

section "fastfetch config"
FF_DIR="$REAL_HOME/.config/fastfetch"
sudo -u "$REAL_USER" mkdir -p "$FF_DIR"
for f in "$SCRIPT_DIR/configs/fastfetch/"*; do
    install -Dm644 "$f" "$FF_DIR/$(basename "$f")"
    chown "$REAL_USER:$REAL_USER" "$FF_DIR/$(basename "$f")"
done
ok "fastfetch config deployed."

section "btop config"
BTOP_DIR="$REAL_HOME/.config/btop"
sudo -u "$REAL_USER" mkdir -p "$BTOP_DIR/themes"
install -Dm644 "$SCRIPT_DIR/configs/btop/btop.conf" "$BTOP_DIR/btop.conf"
for f in "$SCRIPT_DIR/configs/btop/themes/"*; do
    install -Dm644 "$f" "$BTOP_DIR/themes/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$BTOP_DIR"
ok "btop config deployed."

section "cava config"
CAVA_DIR="$REAL_HOME/.config/cava"
sudo -u "$REAL_USER" mkdir -p "$CAVA_DIR/shaders" "$CAVA_DIR/themes"
install -Dm644 "$SCRIPT_DIR/configs/cava/config" "$CAVA_DIR/config"
for f in "$SCRIPT_DIR/configs/cava/shaders/"*; do
    install -Dm644 "$f" "$CAVA_DIR/shaders/$(basename "$f")"
done
for f in "$SCRIPT_DIR/configs/cava/themes/"*; do
    install -Dm644 "$f" "$CAVA_DIR/themes/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$CAVA_DIR"
ok "cava config deployed."

section "alacritty config"
ALA_DIR="$REAL_HOME/.config/alacritty"
sudo -u "$REAL_USER" mkdir -p "$ALA_DIR/themes"
install -Dm644 "$SCRIPT_DIR/configs/alacritty/alacritty.toml" "$ALA_DIR/alacritty.toml"
for f in "$SCRIPT_DIR/configs/alacritty/themes/"*; do
    install -Dm644 "$f" "$ALA_DIR/themes/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$ALA_DIR"
ok "alacritty config deployed."

section "foot config"
FOOT_DIR="$REAL_HOME/.config/foot"
sudo -u "$REAL_USER" mkdir -p "$FOOT_DIR/themes"
for f in "$SCRIPT_DIR/configs/foot/"*.ini; do
    install -Dm644 "$f" "$FOOT_DIR/$(basename "$f")"
done
for f in "$SCRIPT_DIR/configs/foot/themes/"*; do
    install -Dm644 "$f" "$FOOT_DIR/themes/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$FOOT_DIR"
ok "foot config deployed."

section "ghostty config"
GHOSTTY_DIR="$REAL_HOME/.config/ghostty"
sudo -u "$REAL_USER" mkdir -p "$GHOSTTY_DIR/themes"
install -Dm644 "$SCRIPT_DIR/configs/ghostty/config" "$GHOSTTY_DIR/config"
for f in "$SCRIPT_DIR/configs/ghostty/themes/"*; do
    install -Dm644 "$f" "$GHOSTTY_DIR/themes/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$GHOSTTY_DIR"
ok "ghostty config deployed."

section "yazi config"
YAZI_DIR="$REAL_HOME/.config/yazi"
sudo -u "$REAL_USER" mkdir -p "$YAZI_DIR/flavors/noctalia.yazi"
for f in yazi.toml keymap.toml theme.toml; do
    install -Dm644 "$SCRIPT_DIR/configs/yazi/$f" "$YAZI_DIR/$f"
done
for f in "$SCRIPT_DIR/configs/yazi/flavors/noctalia.yazi/"*; do
    install -Dm644 "$f" "$YAZI_DIR/flavors/noctalia.yazi/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$YAZI_DIR"
ok "yazi config deployed."

section "starship config"
install -Dm644 "$SCRIPT_DIR/configs/starship/starship.toml" "$REAL_HOME/.config/starship.toml"
chown "$REAL_USER:$REAL_USER" "$REAL_HOME/.config/starship.toml"
ok "starship config deployed."

section "newsboat config"
NB_DIR="$REAL_HOME/.config/newsboat"
sudo -u "$REAL_USER" mkdir -p "$NB_DIR"
for f in config urls; do
    install -Dm644 "$SCRIPT_DIR/configs/newsboat/$f" "$NB_DIR/$f"
    chown "$REAL_USER:$REAL_USER" "$NB_DIR/$f"
done
ok "newsboat config deployed."

section "easyeffects config"
EE_DIR="$REAL_HOME/.config/easyeffects/db"
sudo -u "$REAL_USER" mkdir -p "$EE_DIR"
for f in "$SCRIPT_DIR/configs/easyeffects/db/"*; do
    install -Dm644 "$f" "$EE_DIR/$(basename "$f")"
done
chown -R "$REAL_USER:$REAL_USER" "$REAL_HOME/.config/easyeffects"
ok "easyeffects config deployed."

section "thefuck config"
TF_DIR="$REAL_HOME/.config/thefuck"
sudo -u "$REAL_USER" mkdir -p "$TF_DIR"
install -Dm644 "$SCRIPT_DIR/configs/thefuck/settings.py" "$TF_DIR/settings.py"
chown "$REAL_USER:$REAL_USER" "$TF_DIR/settings.py"
ok "thefuck config deployed."

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
if sudo -u "$REAL_USER" HOME="$REAL_HOME" \
        bash -c 'command -v claude &>/dev/null'; then
    ok "Claude Code already installed."
else
    info "Installing Claude Code..."
    sudo -u "$REAL_USER" HOME="$REAL_HOME" \
        sh -c "$(curl -fsSL https://claude.ai/install.sh)"
    ok "Claude Code installed."
fi

# ── App installations ─────────────────────────────────────────────────────────

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
for script in runclam.sh url-maintenance.sh; do
    base="${script%.sh}"
    install -Dm755 "$SCRIPT_DIR/apps/neils-scripts/$script" "$SCRIPTS_BIN/$base"
    chown "$REAL_USER:$REAL_USER" "$SCRIPTS_BIN/$base"
done
ok "Scripts installed to $SCRIPTS_BIN/"

# ── Firefox settings ──────────────────────────────────────────────────────────
# Interactive — run separately as yourself after Firefox has been opened once.

section "Firefox settings"
warn "Firefox settings require manual setup (interactive profile selection)."
info "Run as yourself (not sudo) after first launching Firefox:"
info "  cd $SCRIPT_DIR/apps/firefox-settings && bash install.sh"

# ── System services ───────────────────────────────────────────────────────────

section "System services"
systemctl enable bluetooth.service
systemctl enable power-profiles-daemon.service
ok "bluetooth + power-profiles-daemon enabled."

# ── SDDM autologin to mango ───────────────────────────────────────────────────

section "SDDM autologin"
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/autologin.conf <<EOF
[Autologin]
User=$REAL_USER
Session=mango.desktop
EOF
chmod 644 /etc/sddm.conf.d/autologin.conf

# Disable any conflicting display managers that may have been installed.
for dm in gdm lightdm; do
    if systemctl is-enabled "$dm.service" &>/dev/null; then
        info "Disabling $dm.service to avoid conflict with SDDM."
        systemctl disable "$dm.service" || true
    fi
done

systemctl enable sddm.service
# Boot to graphical target so SDDM actually runs.
systemctl set-default graphical.target
ok "SDDM autologin enabled — boots straight into mango as $REAL_USER."

# ── Done ──────────────────────────────────────────────────────────────────────

section "Setup complete"
ok "All packages installed, MangoWM + DMS deployed, configs in place."
info "Reboot now:  sudo reboot"
info "SDDM will autologin and launch mango."
info "If DMS does not appear, check:  cat ~/.config/mango/autostart.log"
