# Fuetem Audio

A desktop audio tool for Linux. Open any audio file, preview it, trim it to exact timestamps, convert it to a different format, and edit its tags — all in one place.

## Features

- **Waveform display** — visual overview of the audio with the trim region highlighted; click or drag to seek
- **Precise trimming** — set start and end times with `HH:MM:SS.mmm` inputs; use the ± buttons to nudge in 100 ms steps, or hit **Set** to snap to the current playback position
- **Loop trim region** — audition your cut on repeat before saving
- **Format conversion** — convert between MP3, FLAC, OPUS, WAV, AAC, M4A, OGG with selectable quality
- **Normalize on export** — apply `loudnorm` to any trim or conversion
- **Split at position** — cut the file in two at the current playback position with no re-encoding
- **Metadata editor** — read and write Title, Artist, Album, Year tags
- **Recording** — record audio from your system input and optionally load it straight into the editor
- **Recent files** — quick access to the last 10 opened files
- **Drag and drop** — drop an audio file onto the window to open it

## Requirements

- Python 3.10+
- PyQt5
- qt5-multimedia + gst-libav (GStreamer backend for playback)
- ffmpeg

On Arch Linux:

```bash
sudo pacman -S python-pyqt5 qt5-multimedia gst-plugins-good gst-libav ffmpeg
```

On Ubuntu/Debian:

```bash
sudo apt install python3-pyqt5 python3-pyqt5.qtmultimedia \
    gstreamer1.0-plugins-good gstreamer1.0-libav ffmpeg
```

## Install

```bash
git clone https://github.com/invisi101/fuetem-audio
cd fuetem-audio
chmod +x install.sh
./install.sh
```

This copies the script to `~/.local/bin/fuetem-audio`, installs the icon, and creates a desktop entry so the app appears in your launcher.

Launch from your app launcher or run:

```bash
fuetem-audio
```

## Uninstall

```bash
rm ~/.local/bin/fuetem-audio
rm ~/.local/share/applications/fuetem-audio.desktop
rm ~/.local/share/icons/hicolor/scalable/apps/fuetem-audio.svg
```
