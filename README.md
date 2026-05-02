# fedora

Personal Fedora 44 setup. Bootstraps a TTY-only base install into a fully
configured MangoWM + DankMaterialShell desktop in one command.

## What it does

- Adds RPM Fusion Free, Terra, COPRs (DMS, Ghostty, Firefox-dev, Zen),
  Brave, Mullvad, and LibreWolf repos
- Installs ~150 packages (terminals, browsers, security tools, dev tools,
  WM runtime, fonts, audio stack)
- Builds and installs scenefx 0.4.1 + MangoWM from source
- Installs DankMaterialShell (DMS)
- Configures UFW (replaces firewalld), Flatpak + Flathub
- Deploys configs for: mango, kitty, alacritty, foot, ghostty, fastfetch,
  btop, cava, yazi, nvim, starship, newsboat, easyeffects, thefuck, zsh
- Installs Oh My Zsh + Powerlevel10k + plugins, JetBrainsMono Nerd Font
- Installs Claude Code
- Builds and installs all bundled apps under `apps/`

## Prerequisites

Fresh Fedora 44 install (Everything netinstall is fine). At install time,
choose NetworkManager so the TTY has wifi/ethernet ready. No desktop
environment needed — this script provides one.

## Deploy from TTY

1. **Log in** as your normal user.

2. **Confirm internet** works:
   ```sh
   ping -c1 fedoraproject.org
   ```
   If wifi isn't up yet:
   ```sh
   nmcli device wifi list
   nmcli device wifi connect "SSID" password "PASSWORD"
   ```

3. **Install git** (it's the only thing not yet installed):
   ```sh
   sudo dnf install -y git
   ```

4. **Clone this repo:**
   ```sh
   mkdir -p ~/dev && cd ~/dev
   git clone https://github.com/invisi101/fedora.git
   cd fedora
   ```

5. **Run the installer** (takes 20–40 min depending on network/CPU):
   ```sh
   sudo bash setup.sh
   ```

6. **Reboot:**
   ```sh
   sudo reboot
   ```

7. **Log into TTY** again, then start MangoWM:
   ```sh
   mango
   ```

## Post-install (manual)

- **Firefox profile path** — open Firefox once, then:
  ```sh
  cd ~/dev/fedora/apps/firefox-settings && bash install.sh
  ```
- **Standard Notes / FreeTube / Blanket / Zen Browser** — already installed
  as Flatpaks; sign in on first launch
- **DMS theming** — DMS auto-generates `~/.config/mango/dms/{cursor,outputs,
  colors,layout}.conf` on first run

## Repo layout

```
.
├── apps/             bundled app sources (yt-snatcher, pikapika, lipcord,
│                     emdee-editor, emdee-viewer, fuetem-audio,
│                     fuetem-imager, firefox-settings, neils-scripts)
├── configs/          all dotfiles deployed by setup.sh
│   ├── mango/        config.conf, binds.conf, screensaver.txt
│   ├── scripts/      mango-screensaver, screenshot-*, clipboard-rofi
│   ├── zsh/          .zshrc, .p10k.zsh
│   ├── fonts/        JetBrainsMono Nerd Font (4 TTFs)
│   └── …             kitty, alacritty, foot, ghostty, fastfetch, btop,
│                     cava, yazi, nvim, starship, newsboat, easyeffects, thefuck
├── lib/              shared shell helpers (logging, RPM Fusion enable)
└── setup.sh          master installer (idempotent — safe to re-run)
```

## Re-running

`setup.sh` is idempotent: every section checks before installing.
Re-running picks up where it left off, applies new configs, and skips
anything already present.

## What's NOT included

- Personal Firefox profile (machine-specific path; install separately)
- Anything that requires interactive sign-in (Brave, Mullvad, etc.)
- GPU drivers (handled by Fedora's kernel + Mesa stack out of the box)
