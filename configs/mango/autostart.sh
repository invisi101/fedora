#!/usr/bin/env bash
# Mango autostart — fired once when mango starts via the single
# `exec-once=` in config.conf. All output is redirected to
# autostart.log so failures are debuggable.

exec 2> "$HOME/.config/mango/autostart.log"
set -x

# Propagate Wayland env to systemd user services and dbus activation
# (synchronous — must complete before backgrounded helpers below).
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE DBUS_SESSION_BUS_ADDRESS
dbus-update-activation-environment --systemd --all

# Optional user session target (no-op if unit not installed).
systemctl --user start mango-session.target 2>/dev/null || true

# Polkit auth agent — required for GUI pkexec prompts (Stacer, etc.).
/usr/libexec/polkit-gnome-authentication-agent-1 &

# Clipboard history (text + images).
wl-paste --watch cliphist store &
wl-paste --type image --watch cliphist store &

# Secrets backend.
gnome-keyring-daemon --start --components=secrets

# Idle / lock — fires the screensaver after 5 min, swaylock before sleep.
swayidle -w \
    timeout 300 "$HOME/.local/bin/mango-launch-screensaver" \
    before-sleep "swaylock" &

# DankMaterialShell.
dms run &
