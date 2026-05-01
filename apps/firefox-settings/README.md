# Firefox Settings

Personal Firefox profile template. Contains all extensions, preferences, bookmarks, and configuration for a fully set up Firefox installation.

The profile zip is stored as a GitHub Release asset (not in the repo itself) due to its size exceeding GitHub's 100 MB file limit.

## What's included

The zip contains a complete Firefox profile directory — everything Firefox stores in its profile folder:

- Extensions and their settings
- Preferences (`prefs.js`)
- Bookmarks and history (`places.sqlite`)
- Security settings and certificates (`cert9.db`, `key4.db`)
- Site permissions (`permissions.sqlite`)
- Search engine configuration
- All other profile data

## Quick start

Open the version of Firefox you want to configure, then close it. Then install `gh` and run the install script:

### Arch Linux

```bash
sudo pacman -S gh --noconfirm && gh auth login
```

```bash
rm -rf /tmp/ff-setup && gh repo clone invisi101/firefox-settings /tmp/ff-setup && /tmp/ff-setup/install.sh && rm -rf /tmp/ff-setup
```

### Debian / Ubuntu / Kali

```bash
(type -p wget >/dev/null || sudo apt install wget -y) \
  && sudo mkdir -p -m 755 /etc/apt/keyrings \
  && out=$(mktemp) \
  && wget -nv -O "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  && cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
  && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && sudo apt update && sudo apt install gh zip unzip -y \
  && gh auth login
```

```bash
rm -rf /tmp/ff-setup && gh repo clone invisi101/firefox-settings /tmp/ff-setup && /tmp/ff-setup/install.sh && rm -rf /tmp/ff-setup
```

### Fedora

```bash
sudo dnf install gh -y && gh auth login
```

```bash
rm -rf /tmp/ff-setup && gh repo clone invisi101/firefox-settings /tmp/ff-setup && /tmp/ff-setup/install.sh && rm -rf /tmp/ff-setup
```

### macOS

```bash
brew install gh && gh auth login
```

```bash
rm -rf /tmp/ff-setup && gh repo clone invisi101/firefox-settings /tmp/ff-setup && /tmp/ff-setup/install.sh && rm -rf /tmp/ff-setup
```

### What the script does

- Scans for Firefox profile directories across all common locations
- Shows every detected Firefox installation (regular, ESR, Developer Edition)
- Asks you to select which one to install settings to
- Backs up the existing profile as a timestamped zip before overwriting
- Downloads the profile zip from the GitHub release
- Extracts it into the selected profile directory
- Asks whether to apply [arkenfox](https://github.com/arkenfox/user.js) privacy hardening
  - If yes: downloads the latest arkenfox `user.js` and `updater.sh`, copies in `user-overrides.js` from this repo
  - If no: skips, leaving just the base profile
- Restart Firefox to apply the settings

### Supported Firefox editions

| Edition | Profile pattern |
|---------|----------------|
| Firefox | `*.default-release` |
| Firefox ESR | `*.default-esr` |
| Firefox Developer Edition | `*.dev-edition-default` |

### Supported profile locations

The script checks all of these automatically:

| Location | Platform |
|----------|----------|
| `~/.mozilla/firefox/` | Most Linux distros |
| `~/.config/mozilla/firefox/` | Arch Linux |
| `~/.var/app/org.mozilla.firefox/.mozilla/firefox/` | Flatpak |
| `~/snap/firefox/common/.mozilla/firefox/` | Snap |
| `~/Library/Application Support/Firefox/Profiles/` | macOS |

## Updating settings

When you've made changes to your Firefox configuration and want to save them:

1. Close Firefox.

2. Create a new zip from your current profile:

   ```bash
   cd ~/.config/mozilla/firefox/*.default-release
   zip -r ~/dev/firefox-settings/ff-profile.zip .
   ```

   Adjust the path if your profile is in a different location (e.g. `~/.mozilla/firefox/*.default-release`).

3. Upload the updated zip to the GitHub release:

   ```bash
   ./update-settings.sh
   ```

   This replaces the existing `ff-profile.zip` on the `v1.0` release.

## Warning

This will **overwrite** all Firefox settings, extensions, bookmarks, and data in the target profile. Do not run this on a Firefox installation that has data you want to keep unless you have backed it up first.
