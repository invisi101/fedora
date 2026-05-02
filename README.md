# fedora

Personal Fedora 44 setup. Bootstraps a TTY-only base install into a fully
configured MangoWM + DankMaterialShell desktop in one command.

## What it does

- Adds RPM Fusion Free, Terra (priority-pinned), COPRs (DMS, Ghostty),
  and Brave repos
- Installs ~140 packages (terminals, firefox/brave/tor browsers,
  security tools, dev tools, WM runtime, fonts, audio stack, bluetooth,
  power-profiles-daemon, SDDM)
- Installs MangoWM from Terra (already built against scenefx 0.4 + wlroots 0.19)
- Installs DankMaterialShell (DMS) from the avengemedia/dms COPR
- Configures UFW (replaces firewalld), Flatpak + Flathub
- Deploys configs for: mango, kitty, alacritty, foot, ghostty, fastfetch,
  btop, cava, yazi, starship, newsboat, easyeffects, thefuck, zsh
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

5. **Run the installer** (takes ~10–20 min depending on network):
   ```sh
   sudo bash setup.sh
   ```

6. **Reboot:**
   ```sh
   sudo reboot
   ```

7. **Boot straight into MangoWM** — SDDM autologins as your user and
   launches the mango session. No manual `mango` command needed.

## Post-install (manual)

- **Firefox profile path** — open Firefox once, then:
  ```sh
  cd ~/dev/fedora/apps/firefox-settings && bash install.sh
  ```
- **Standard Notes / FreeTube / Blanket** — already installed as
  Flatpaks; sign in on first launch
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
│                     cava, yazi, starship, newsboat, easyeffects, thefuck
├── lib/              shared shell helpers (logging, RPM Fusion enable)
└── setup.sh          master installer (idempotent — safe to re-run)
```

## Re-running

`setup.sh` is idempotent: every section checks before installing.
Re-running picks up where it left off, applies new configs, and skips
anything already present.

## If it breaks

The script uses `set -euo pipefail`, so any failed command halts the
run with an error. **In almost every case, the right move is to read
the error, fix the immediate issue, and just re-run `sudo bash setup.sh`.**

### During install

| Symptom | Likely cause | Action |
|---|---|---|
| `Failed to download metadata for repo 'terra'` | network blip, Terra mirror temporarily down | wait a minute, re-run |
| `No match for argument: mangowm` | Terra repo didn't enable cleanly | `sudo dnf repolist` — confirm `terra` is listed; if not, re-run setup.sh (Terra section is idempotent) |
| `dnf install -y dms` fails | DMS COPR build for Fedora 44 not yet published | the script automatically falls back to `curl https://install.danklinux.com \| sh` |
| `pipx install` fails for tte/unimatrix | PyPI rate limit or network | re-run; pipx is idempotent |
| App install.sh aborts mid-script | one of the bundled apps has a bug | re-run setup.sh — completed sections are skipped, the failing app re-attempts |
| Sudo timeout mid-run | very long-running step | re-run; you'll only be prompted once at the start |

### After reboot — black screen / SDDM loop / mango won't start

Press **`Ctrl+Alt+F2`** (or F3, F4) to drop to a TTY. Log in there, then:

```sh
# Check display manager
journalctl -b -u sddm | tail -50

# Check what mango's autostart did (or didn't do)
cat ~/.config/mango/autostart.log

# Check user-level systemd services
systemctl --user status

# Try mango by hand (without SDDM autologin getting in the way)
sudo systemctl stop sddm
mango
```

If mango itself crashes immediately, run it with stderr captured:

```sh
mango 2> ~/mango-crash.log
cat ~/mango-crash.log
```

### Disable autologin to recover

If SDDM keeps autologin-looping, kill the autologin so you get the
SDDM login screen (or the TTY) instead:

```sh
sudo rm /etc/sddm.conf.d/autologin.conf
sudo systemctl restart sddm    # or: systemctl set-default multi-user.target && reboot
```

You can re-run `sudo bash setup.sh` to put autologin back once the
underlying issue is fixed.

### DMS doesn't appear (mango runs but no shell)

```sh
# Inside a mango terminal
dms run                       # try launching by hand — error goes to stdout
cat ~/.config/mango/autostart.log
journalctl --user -b | grep -i dms
```

If `dms run` works manually, the autostart.sh order/race is suspect —
check the log for which line errored.

### Audio / bluetooth not working

```sh
systemctl --user status pipewire pipewire-pulse wireplumber
systemctl status bluetooth
```

`pipewire-pulse` should be active for both PipeWire and PulseAudio
clients. `bluetooth.service` is enabled by setup.sh; firmware comes
from the `Hardware Support` add-on.

### Fonts look broken / missing glyphs

```sh
fc-list | grep -i jetbrains    # should list 4 TTFs
fc-cache -fv                    # rebuild cache
```

Fonts are deployed to `~/.local/share/fonts/JetBrainsMonoNF/`. If
they're missing, re-run setup.sh.

### Last resort

Read the section header that failed (each is wrapped in `━━━` banners
in the output) and search for it in `setup.sh` to see what command
ran. The script's plain bash — every step is grep-able and editable.

## What's NOT included

- Personal Firefox profile (machine-specific path; install separately)
- Anything that requires interactive sign-in (Brave, etc.)
- GPU drivers (handled by Fedora's kernel + Mesa stack out of the box)
