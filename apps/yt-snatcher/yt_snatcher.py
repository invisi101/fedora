#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

SAVE_DIR = str(Path.home() / "Downloads" / "ytdlp")

OUTPUT_TEMPLATES = [
    ("Default (Title)", "%(title)s.%(ext)s"),
    ("Title [ID]", "%(title)s [%(id)s].%(ext)s"),
    ("Channel - Title", "%(channel)s - %(title)s.%(ext)s"),
    ("Playlist folder", "%(playlist_title)s/%(playlist_index)03d - %(title)s.%(ext)s"),
]

# --- DD-imager Neon Theme (QSS) ---
NEON_STYLESHEET = """
/* === Window === */
QWidget#MainWindow {
    background: qlineargradient(y1:0, y2:1,
        stop:0 #0f0f23, stop:1 #12122e);
}

/* === Labels === */
QLabel {
    color: #e0e0ff;
}

QLabel#brandLarge, QLabel#brandSmall {
    color: #f472b6;
    padding-top: 10px;
    padding-bottom: 10px;
}

QFrame#menuBar {
    background: transparent;
}

QLabel#subtitleLabel {
    color: rgba(196, 196, 240, 0.5);
    font-size: 18px;
}

QLabel#sectionLabel {
    color: #f472b6;
    font-weight: 600;
    font-size: 18px;
    letter-spacing: 0.5px;
}

QLabel#statusLabel {
    color: #a5b4fc;
    font-size: 18px;
}

/* === Line Edit === */
QLineEdit {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 8px;
    color: #e0e0ff;
    padding: 8px 12px;
    font-size: 18px;
    selection-background-color: #818cf8;
}

QLineEdit:focus {
    border: 1px solid #818cf8;
}

QLineEdit::placeholder {
    color: rgba(196, 196, 240, 0.35);
}

/* === Checkboxes === */
QCheckBox {
    color: #c4c4f0;
    spacing: 6px;
    font-size: 18px;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 5px;
    border: 2px solid #2d2d5e;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    border: 2px solid #818cf8;
}

QCheckBox::indicator:hover {
    border-color: #818cf8;
}

/* === ComboBox === */
QComboBox {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 8px;
    color: #e0e0ff;
    padding: 6px 12px;
    font-size: 18px;
    min-width: 90px;
}

QComboBox:focus, QComboBox:hover {
    border: 1px solid #818cf8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #818cf8;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    border: 1px solid #2d2d5e;
    color: #e0e0ff;
    selection-background-color: rgba(129, 140, 248, 0.3);
    selection-color: #e0e0ff;
    outline: none;
}

/* === SpinBox === */
QSpinBox {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 8px;
    color: #e0e0ff;
    padding: 6px 12px;
    font-size: 18px;
}

QSpinBox:focus, QSpinBox:hover {
    border: 1px solid #818cf8;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #2d2d5e;
    border: none;
    width: 18px;
}

QSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #818cf8;
}

QSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #818cf8;
}

/* === ScrollArea === */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #0f0f23;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: rgba(129, 140, 248, 0.3);
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(129, 140, 248, 0.5);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #1a1a2e;
    border: 1px solid #2d2d5e;
    border-radius: 10px;
    min-height: 20px;
    max-height: 20px;
    text-align: center;
    color: #e0e0ff;
    font-weight: bold;
    font-size: 16px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, x2:1,
        stop:0 #34d399, stop:0.5 #06b6d4, stop:1 #818cf8);
    border-radius: 9px;
}

/* === Download Button === */
QPushButton#downloadBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 26px;
    font-size: 18px;
    font-weight: 600;
}

QPushButton#downloadBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f9a8d4, stop:1 #a5b4fc);
}

QPushButton#downloadBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ec4899, stop:1 #6366f1);
}

QPushButton#downloadBtn:disabled {
    background: #2d2d5e;
    color: rgba(196, 196, 240, 0.4);
}

/* === Cancel Button === */
QPushButton#cancelBtn {
    background-color: transparent;
    color: #f472b6;
    border: 1px solid rgba(244, 114, 182, 0.3);
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 18px;
    font-weight: 500;
}

QPushButton#cancelBtn:hover {
    border-color: rgba(244, 114, 182, 0.6);
    background-color: rgba(244, 114, 182, 0.1);
}

/* === Close Button === */
QPushButton#closeBtn {
    background-color: transparent;
    color: #c4c4f0;
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 18px;
    font-weight: 500;
}

QPushButton#closeBtn:hover {
    border-color: rgba(129, 140, 248, 0.6);
    color: #e0e0ff;
    background-color: rgba(129, 140, 248, 0.1);
}

/* === Back Button === */
QPushButton#backBtn {
    background-color: transparent;
    color: #818cf8;
    border: none;
    font-size: 18px;
    font-weight: 500;
    padding: 4px 8px;
}

QPushButton#backBtn:hover {
    color: #a5b4fc;
}

/* === Options Button === */
QPushButton#optionsBtn {
    background-color: transparent;
    color: #06b6d4;
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 18px;
    font-weight: 500;
}

QPushButton#optionsBtn:hover {
    border-color: rgba(6, 182, 212, 0.6);
    background-color: rgba(6, 182, 212, 0.1);
}

/* === Card frame === */
QFrame#card {
    background-color: #1a1a2e;
    border: 1px solid rgba(129, 140, 248, 0.15);
    border-radius: 12px;
}

/* === Mode card === */
QFrame#modeCard {
    background-color: #1a1a2e;
    border: 1px solid rgba(129, 140, 248, 0.2);
    border-radius: 16px;
}

QFrame#modeCard:hover {
    border: 1px solid rgba(129, 140, 248, 0.5);
    background-color: rgba(129, 140, 248, 0.05);
}

/* === Separator === */
QFrame#separator {
    background-color: rgba(129, 140, 248, 0.12);
    max-height: 1px;
}

/* === Message boxes === */
QMessageBox {
    background-color: #1a1a2e;
}

QMessageBox QLabel {
    color: #e0e0ff;
    font-size: 14px;
}

QMessageBox QPushButton {
    background-color: #2d2d5e;
    color: #e0e0ff;
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-radius: 6px;
    padding: 6px 20px;
    font-size: 14px;
}

QMessageBox QPushButton:hover {
    background-color: rgba(129, 140, 248, 0.2);
    border-color: #818cf8;
}
"""


# --- Utility ---
def clean_url(url: str) -> str:
    """Sanitize pasted URLs from zsh/Qt weirdness."""
    url = url.strip()
    url = url.replace("\\", "")
    url = url.replace("%5C", "")
    url = url.replace(" ", "")
    url = re.sub(r"https:/*", "https://", url)
    url = re.sub(r"http:/*", "http://", url)
    return url


# --- Worker thread ---
class YTDLPWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    status_update = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, url: str, options: dict):
        super().__init__()
        self.url = url
        self.options = options
        self._process = None
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def _build_command(self):
        opts = self.options
        cmd = ["yt-dlp", "--newline"]

        if opts.get("video_mode"):
            # --- Video ---
            res = opts.get("resolution", "best")
            if res == "best":
                cmd.extend(["-f", "bestvideo+bestaudio/best"])
            else:
                h = res.replace("p", "")
                cmd.extend(
                    ["-f", f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"]
                )
            cmd.extend(["--merge-output-format", opts.get("container", "mp4")])
            cmd.extend(["--embed-metadata", "--embed-thumbnail"])
        else:
            # --- Audio ---
            cmd.extend(["-x", "--audio-format", opts.get("audio_format", "mp3"),
                        "--no-keep-video"])
            quality = opts.get("audio_quality", "best")
            qmap = {
                "best": "0", "320K": "320K", "256K": "256K",
                "192K": "192K", "128K": "128K", "96K": "96K",
            }
            cmd.extend(["--audio-quality", qmap.get(quality, "0")])
            cmd.append("--embed-thumbnail")
            if not opts.get("strip_metadata"):
                cmd.extend([
                    "--embed-metadata",
                    "--parse-metadata", "title:%(title)s",
                    "--parse-metadata", "uploader:%(artist)s",
                ])

        # Combined ffmpeg postprocessor args
        ff = []
        if opts.get("strip_metadata") and not opts.get("video_mode"):
            ff.append("-map_metadata -1")
        if opts.get("normalize_audio") and not opts.get("video_mode"):
            ff.append("-af loudnorm")
        if ff:
            cmd.extend(["--postprocessor-args", "ffmpeg:" + " ".join(ff)])

        # Chapters
        if opts.get("embed_chapters"):
            cmd.append("--embed-chapters")
        if opts.get("split_chapters"):
            cmd.append("--split-chapters")
        if opts.get("download_sections"):
            cmd.extend(["--download-sections", opts["download_sections"]])

        # Subtitles
        if opts.get("write_subs"):
            cmd.append("--write-subs")
        if opts.get("write_auto_subs"):
            cmd.append("--write-auto-subs")
        if opts.get("embed_subs") and opts.get("video_mode"):
            cmd.append("--embed-subs")
        if opts.get("sub_langs"):
            cmd.extend(["--sub-langs", opts["sub_langs"]])
        if opts.get("sub_format"):
            cmd.extend(["--sub-format", opts["sub_format"]])

        # SponsorBlock
        if opts.get("sb_remove") or opts.get("remove_sponsors"):
            cmd.extend(["--sponsorblock-remove", "all"])
        elif opts.get("sb_mark"):
            cmd.extend(["--sponsorblock-mark", "all"])

        # Playlist
        if opts.get("no_playlist"):
            cmd.append("--no-playlist")
        if opts.get("playlist_items"):
            cmd.extend(["--playlist-items", opts["playlist_items"]])
        if opts.get("download_archive") and opts.get("archive_path"):
            cmd.extend(["--download-archive", opts["archive_path"]])

        # Cookies
        browser = opts.get("cookies_browser", "none")
        if browser and browser != "none":
            cmd.extend(["--cookies-from-browser", browser])

        # Download behavior
        frags = opts.get("concurrent_fragments", 1)
        if frags > 1:
            cmd.extend(["--concurrent-fragments", str(frags)])
        if opts.get("rate_limit"):
            cmd.extend(["--limit-rate", opts["rate_limit"]])
        if opts.get("no_overwrites"):
            cmd.append("--no-overwrites")

        # Output
        save_dir = opts.get("save_dir", SAVE_DIR)
        template = opts.get("output_template", "%(title)s.%(ext)s")
        cmd.extend(["--restrict-filenames", "-P", save_dir, "--output", template])

        cmd.append(self.url)
        return cmd

    def run(self):
        save_dir = self.options.get("save_dir", SAVE_DIR)
        os.makedirs(save_dir, exist_ok=True)
        cmd = self._build_command()
        last_line = ""

        try:
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError as e:
            self.finished.emit(False, f"yt-dlp not found: {e}")
            return

        progress_re = re.compile(r"(\d+(?:\.\d+)?)%")
        playlist_re = re.compile(
            r"\[download\]\s+Downloading\s+(?:video|item)\s+(\d+)\s+of\s+(\d+)"
        )

        if self._process.stdout:
            for line in self._process.stdout:
                if self._cancelled:
                    break
                line = line.rstrip()
                last_line = line

                pm = playlist_re.search(line)
                if pm:
                    self.status_update.emit(
                        f"Downloading video {pm.group(1)} of {pm.group(2)}"
                    )

                if "[download]" in line and "%" in line:
                    m = progress_re.search(line)
                    if m:
                        try:
                            self.progress.emit(int(float(m.group(1))))
                        except ValueError:
                            pass

        ret = self._process.wait()
        if self._cancelled:
            self.finished.emit(False, "Download cancelled.")
        else:
            self.finished.emit(ret == 0, last_line)


# --- Clickable mode card ---
class ModeCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal()

    def __init__(self, icon_text, title, subtitle):
        super().__init__()
        self.setObjectName("modeCard")
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedSize(240, 180)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setAlignment(QtCore.Qt.AlignCenter)
        lay.setSpacing(6)

        icon = QtWidgets.QLabel(icon_text)
        icon.setAlignment(QtCore.Qt.AlignCenter)
        icon.setStyleSheet(
            "font-size: 42px; background: transparent; border: none;"
        )
        lay.addWidget(icon)

        t = QtWidgets.QLabel(title)
        t.setAlignment(QtCore.Qt.AlignCenter)
        t.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #e0e0ff;"
            " background: transparent; border: none;"
        )
        lay.addWidget(t)

        s = QtWidgets.QLabel(subtitle)
        s.setAlignment(QtCore.Qt.AlignCenter)
        s.setWordWrap(True)
        s.setStyleSheet(
            "font-size: 14px; color: rgba(196, 196, 240, 0.6);"
            " background: transparent; border: none;"
        )
        lay.addWidget(s)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# --- Main GUI ---
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("YT Snatcher")
        self.setMinimumSize(700, 520)

        self.is_video_mode = False
        self.playlist_status = ""
        self.worker = None

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.stacked = QtWidgets.QStackedWidget()
        outer.addWidget(self.stacked)

        self.stacked.addWidget(self._build_welcome_page())
        self.stacked.addWidget(self._build_download_page())
        self.stacked.addWidget(self._build_options_page())

    # ---- helpers ----

    def _make_menu_bar(self, large=False, back_target=None):
        h = 80 if large else 40
        bar = QtWidgets.QFrame()
        bar.setObjectName("menuBar")
        bar.setMinimumHeight(h)
        bar_lay = QtWidgets.QHBoxLayout(bar)
        bar_lay.setContentsMargins(29, 0, 24, 0)
        bar_lay.setSpacing(0)

        label = QtWidgets.QLabel("YT Snatcher")
        label.setObjectName("brandLarge" if large else "brandSmall")
        font = QtGui.QFont("Vegan Style Personal Use")
        font.setPixelSize(36 if large else 28)
        font.setBold(True)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        bar_lay.addWidget(label)

        bar_lay.addStretch(1)

        if back_target is not None:
            back = QtWidgets.QPushButton("\u2190 Back")
            back.setObjectName("backBtn")
            back.setCursor(QtCore.Qt.PointingHandCursor)
            back.clicked.connect(back_target)
            bar_lay.addWidget(back, alignment=QtCore.Qt.AlignVCenter)

        return bar

    def _make_card(self, title=None):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)
        if title:
            lbl = QtWidgets.QLabel(title)
            lbl.setObjectName("sectionLabel")
            lay.addWidget(lbl)
        return card, lay

    # ---- Page 0: Welcome ----

    def _build_welcome_page(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 40)
        lay.setSpacing(12)

        lay.addWidget(self._make_menu_bar(large=True))

        lay.addStretch(1)

        sub = QtWidgets.QLabel("Snatch audio & video from YouTube")
        sub.setObjectName("subtitleLabel")
        sub.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(28)

        cards = QtWidgets.QHBoxLayout()
        cards.setSpacing(24)
        cards.addStretch(1)

        audio_card = ModeCard(
            "\u266b", "Audio", "Download as MP3, FLAC,\nWAV & more"
        )
        audio_card.clicked.connect(lambda: self._go_to_download(False))
        cards.addWidget(audio_card)

        video_card = ModeCard(
            "\u25b6", "Video", "Download as MP4, MKV,\nWebM & more"
        )
        video_card.clicked.connect(lambda: self._go_to_download(True))
        cards.addWidget(video_card)

        cards.addStretch(1)
        lay.addLayout(cards)

        lay.addStretch(2)
        return page

    # ---- Page 1: Download ----

    def _build_download_page(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 12, 0, 16)
        lay.setSpacing(10)

        lay.addWidget(self._make_menu_bar(back_target=self._go_to_welcome))

        # Content area with side margins
        content = QtWidgets.QVBoxLayout()
        content.setContentsMargins(24, 0, 24, 0)
        content.setSpacing(10)

        # URL card
        url_card, url_lay = self._make_card("URL")
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL\u2026")
        self.url_input.setClearButtonEnabled(True)
        url_lay.addWidget(self.url_input)
        content.addWidget(url_card)

        # Format card
        fmt_card, fmt_lay = self._make_card("FORMAT")

        # Audio row
        self.audio_format_row = QtWidgets.QWidget()
        af = QtWidgets.QHBoxLayout(self.audio_format_row)
        af.setContentsMargins(0, 0, 0, 0)
        af.addWidget(QtWidgets.QLabel("Format:"))
        self.audio_format_combo = QtWidgets.QComboBox()
        self.audio_format_combo.addItems(
            ["mp3", "flac", "opus", "wav", "aac", "m4a", "vorbis"]
        )
        af.addWidget(self.audio_format_combo)
        af.addSpacing(14)
        af.addWidget(QtWidgets.QLabel("Quality:"))
        self.audio_quality_combo = QtWidgets.QComboBox()
        self.audio_quality_combo.addItems(
            ["best", "320K", "256K", "192K", "128K", "96K"]
        )
        af.addWidget(self.audio_quality_combo)
        af.addStretch(1)
        fmt_lay.addWidget(self.audio_format_row)

        # Video row
        self.video_format_row = QtWidgets.QWidget()
        vf = QtWidgets.QHBoxLayout(self.video_format_row)
        vf.setContentsMargins(0, 0, 0, 0)
        vf.addWidget(QtWidgets.QLabel("Resolution:"))
        self.resolution_combo = QtWidgets.QComboBox()
        self.resolution_combo.addItems(
            ["best", "2160p", "1080p", "720p", "480p", "360p"]
        )
        vf.addWidget(self.resolution_combo)
        vf.addSpacing(14)
        vf.addWidget(QtWidgets.QLabel("Container:"))
        self.container_combo = QtWidgets.QComboBox()
        self.container_combo.addItems(["mp4", "mkv", "webm"])
        vf.addWidget(self.container_combo)
        vf.addStretch(1)
        fmt_lay.addWidget(self.video_format_row)

        content.addWidget(fmt_card)

        # Quick options card
        opts_card, opts_lay = self._make_card("OPTIONS")

        self.strip_metadata = QtWidgets.QCheckBox("Strip metadata")
        self.normalize_audio = QtWidgets.QCheckBox("Normalize audio")
        self.audio_opts = [self.strip_metadata, self.normalize_audio]

        self.quick_embed_subs = QtWidgets.QCheckBox("Embed subtitles")
        self.video_opts = [self.quick_embed_subs]

        self.quick_embed_chapters = QtWidgets.QCheckBox("Embed chapters")
        self.quick_remove_sponsors = QtWidgets.QCheckBox("Remove sponsors")

        for w in self.audio_opts:
            opts_lay.addWidget(w)
        for w in self.video_opts:
            opts_lay.addWidget(w)
        opts_lay.addWidget(self.quick_embed_chapters)
        opts_lay.addWidget(self.quick_remove_sponsors)
        self.no_playlist = QtWidgets.QCheckBox(
            "Single video only (no playlist)"
        )
        opts_lay.addWidget(self.no_playlist)

        content.addWidget(opts_card)

        # Advanced options button
        adv = QtWidgets.QPushButton("Advanced Options")
        adv.setObjectName("optionsBtn")
        adv.setCursor(QtCore.Qt.PointingHandCursor)
        adv.clicked.connect(self._go_to_options)
        content.addWidget(adv, alignment=QtCore.Qt.AlignLeft)

        content.addStretch(1)

        # Progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        content.addWidget(self.progress_bar)

        self.status_label = QtWidgets.QLabel("Idle.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        content.addWidget(self.status_label)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)

        self.download_btn = QtWidgets.QPushButton("Download")
        self.download_btn.setObjectName("downloadBtn")
        self.download_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self.start_download)
        btn_row.addWidget(self.download_btn)

        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.hide()
        btn_row.addWidget(self.cancel_btn)

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.hide()
        btn_row.addWidget(self.close_btn)

        btn_row.addStretch(1)
        content.addLayout(btn_row)

        lay.addLayout(content)

        return page

    # ---- Page 2: Advanced Options ----

    def _build_options_page(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 12, 0, 16)
        lay.setSpacing(10)

        lay.addWidget(self._make_menu_bar(
            back_target=lambda: self.stacked.setCurrentIndex(1)
        ))

        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        content = QtWidgets.QWidget()
        cl = QtWidgets.QVBoxLayout(content)
        cl.setContentsMargins(24, 0, 34, 0)
        cl.setSpacing(14)

        # -- SUBTITLES --
        sub_card, sl = self._make_card("SUBTITLES")
        self.write_subs = QtWidgets.QCheckBox("Write subtitle files")
        self.write_auto_subs = QtWidgets.QCheckBox(
            "Write auto-generated subtitles"
        )
        self.adv_embed_subs = QtWidgets.QCheckBox("Embed subtitles in video")
        sl.addWidget(self.write_subs)
        sl.addWidget(self.write_auto_subs)
        sl.addWidget(self.adv_embed_subs)

        lr = QtWidgets.QHBoxLayout()
        lr.addWidget(QtWidgets.QLabel("Languages:"))
        self.sub_langs = QtWidgets.QLineEdit()
        self.sub_langs.setPlaceholderText("en,es,fr")
        lr.addWidget(self.sub_langs)
        sl.addLayout(lr)

        fr = QtWidgets.QHBoxLayout()
        fr.addWidget(QtWidgets.QLabel("Format:"))
        self.sub_format = QtWidgets.QComboBox()
        self.sub_format.addItems(["srt", "vtt", "ass"])
        fr.addWidget(self.sub_format)
        fr.addStretch(1)
        sl.addLayout(fr)
        cl.addWidget(sub_card)

        # -- SPONSORBLOCK --
        sb_card, sbl = self._make_card("SPONSORBLOCK")
        self.sb_mark = QtWidgets.QCheckBox(
            "Mark sponsored segments as chapters"
        )
        self.sb_remove = QtWidgets.QCheckBox("Remove sponsored segments")
        sbl.addWidget(self.sb_mark)
        sbl.addWidget(self.sb_remove)
        cl.addWidget(sb_card)

        # -- CHAPTERS & SECTIONS --
        ch_card, chl = self._make_card("CHAPTERS & SECTIONS")
        self.adv_embed_chapters = QtWidgets.QCheckBox("Embed chapters")
        self.split_chapters = QtWidgets.QCheckBox("Split by chapters")
        chl.addWidget(self.adv_embed_chapters)
        chl.addWidget(self.split_chapters)

        sr = QtWidgets.QHBoxLayout()
        sr.addWidget(QtWidgets.QLabel("Time range:"))
        self.download_sections = QtWidgets.QLineEdit()
        self.download_sections.setPlaceholderText("*00:30-01:45")
        sr.addWidget(self.download_sections)
        chl.addLayout(sr)
        cl.addWidget(ch_card)

        # -- PLAYLIST --
        pl_card, pll = self._make_card("PLAYLIST")

        pi = QtWidgets.QHBoxLayout()
        pi.addWidget(QtWidgets.QLabel("Items:"))
        self.playlist_items = QtWidgets.QLineEdit()
        self.playlist_items.setPlaceholderText("1-5,8,10-12")
        pi.addWidget(self.playlist_items)
        pll.addLayout(pi)

        self.download_archive = QtWidgets.QCheckBox("Use download archive")
        pll.addWidget(self.download_archive)

        ar = QtWidgets.QHBoxLayout()
        ar.addWidget(QtWidgets.QLabel("Archive file:"))
        self.archive_path = QtWidgets.QLineEdit()
        self.archive_path.setPlaceholderText("Path to archive file")
        ar.addWidget(self.archive_path)
        pll.addLayout(ar)
        cl.addWidget(pl_card)

        # -- COOKIES --
        ck_card, ckl = self._make_card("COOKIES")
        br = QtWidgets.QHBoxLayout()
        br.addWidget(QtWidgets.QLabel("Browser:"))
        self.cookies_browser = QtWidgets.QComboBox()
        self.cookies_browser.addItems(
            ["none", "firefox", "chrome", "chromium", "brave", "edge", "vivaldi"]
        )
        br.addWidget(self.cookies_browser)
        br.addStretch(1)
        ckl.addLayout(br)
        cl.addWidget(ck_card)

        # -- DOWNLOAD BEHAVIOR --
        dl_card, dll = self._make_card("DOWNLOAD BEHAVIOR")

        fg = QtWidgets.QHBoxLayout()
        fg.addWidget(QtWidgets.QLabel("Concurrent fragments:"))
        self.concurrent_fragments = QtWidgets.QSpinBox()
        self.concurrent_fragments.setRange(1, 16)
        self.concurrent_fragments.setValue(1)
        fg.addWidget(self.concurrent_fragments)
        fg.addStretch(1)
        dll.addLayout(fg)

        rl = QtWidgets.QHBoxLayout()
        rl.addWidget(QtWidgets.QLabel("Rate limit:"))
        self.rate_limit = QtWidgets.QLineEdit()
        self.rate_limit.setPlaceholderText("e.g. 1M, 500K")
        rl.addWidget(self.rate_limit)
        dll.addLayout(rl)

        self.no_overwrites = QtWidgets.QCheckBox(
            "Don't overwrite existing files"
        )
        dll.addWidget(self.no_overwrites)
        cl.addWidget(dl_card)

        # -- OUTPUT --
        out_card, ol = self._make_card("OUTPUT")

        tr = QtWidgets.QHBoxLayout()
        tr.addWidget(QtWidgets.QLabel("Filename:"))
        self.output_template_combo = QtWidgets.QComboBox()
        for display, _ in OUTPUT_TEMPLATES:
            self.output_template_combo.addItem(display)
        tr.addWidget(self.output_template_combo)
        ol.addLayout(tr)

        dr = QtWidgets.QHBoxLayout()
        dr.addWidget(QtWidgets.QLabel("Save to:"))
        self.save_dir_input = QtWidgets.QLineEdit(SAVE_DIR)
        dr.addWidget(self.save_dir_input)
        ol.addLayout(dr)
        cl.addWidget(out_card)

        cl.addStretch(1)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        return page

    # ---- navigation ----

    def _go_to_download(self, video_mode):
        self.is_video_mode = video_mode
        self.audio_format_row.setVisible(not video_mode)
        self.video_format_row.setVisible(video_mode)
        for w in self.audio_opts:
            w.setVisible(not video_mode)
        for w in self.video_opts:
            w.setVisible(video_mode)
        self.stacked.setCurrentIndex(1)

    def _go_to_welcome(self):
        self.stacked.setCurrentIndex(0)

    def _go_to_options(self):
        self.stacked.setCurrentIndex(2)

    # ---- gather all options ----

    def _gather_options(self):
        return {
            "video_mode": self.is_video_mode,
            # Audio
            "audio_format": self.audio_format_combo.currentText(),
            "audio_quality": self.audio_quality_combo.currentText(),
            # Video
            "resolution": self.resolution_combo.currentText(),
            "container": self.container_combo.currentText(),
            # Quick options
            "strip_metadata": self.strip_metadata.isChecked(),
            "normalize_audio": self.normalize_audio.isChecked(),
            "embed_chapters": (
                self.quick_embed_chapters.isChecked()
                or self.adv_embed_chapters.isChecked()
            ),
            "remove_sponsors": self.quick_remove_sponsors.isChecked(),
            "embed_subs": (
                self.quick_embed_subs.isChecked()
                or self.adv_embed_subs.isChecked()
            ),
            # Advanced — subtitles
            "write_subs": self.write_subs.isChecked(),
            "write_auto_subs": self.write_auto_subs.isChecked(),
            "sub_langs": self.sub_langs.text().strip(),
            "sub_format": self.sub_format.currentText(),
            # Advanced — sponsorblock
            "sb_mark": self.sb_mark.isChecked(),
            "sb_remove": self.sb_remove.isChecked(),
            # Advanced — chapters
            "split_chapters": self.split_chapters.isChecked(),
            "download_sections": self.download_sections.text().strip(),
            # Advanced — playlist
            "no_playlist": self.no_playlist.isChecked(),
            "playlist_items": self.playlist_items.text().strip(),
            "download_archive": self.download_archive.isChecked(),
            "archive_path": self.archive_path.text().strip(),
            # Advanced — cookies
            "cookies_browser": self.cookies_browser.currentText(),
            # Advanced — download behavior
            "concurrent_fragments": self.concurrent_fragments.value(),
            "rate_limit": self.rate_limit.text().strip(),
            "no_overwrites": self.no_overwrites.isChecked(),
            # Advanced — output
            "output_template": OUTPUT_TEMPLATES[
                self.output_template_combo.currentIndex()
            ][1],
            "save_dir": self.save_dir_input.text().strip() or SAVE_DIR,
        }

    # ---- download actions ----

    def start_download(self):
        url = clean_url(self.url_input.text())
        if not url.startswith("http"):
            QtWidgets.QMessageBox.warning(
                self, "Invalid URL", "Please enter a valid URL."
            )
            return

        opts = self._gather_options()

        # Validate rate limit
        if opts["rate_limit"] and not re.match(
            r"^\d+[KkMm]?$", opts["rate_limit"]
        ):
            QtWidgets.QMessageBox.warning(
                self, "Invalid Rate Limit",
                "Rate limit should be like 1M, 500K, etc.",
            )
            return

        # Validate playlist items
        if opts["playlist_items"] and not re.match(
            r"^[\d,\- ]+$", opts["playlist_items"]
        ):
            QtWidgets.QMessageBox.warning(
                self, "Invalid Playlist Items",
                "Playlist items should be like 1-5,8,10-12",
            )
            return

        # Playlist detection
        if re.search(r"playlist\?list=|&list=|/playlist/", url):
            if not opts["no_playlist"]:
                reply = QtWidgets.QMessageBox.question(
                    self, "Playlist Detected",
                    "This URL appears to be a playlist.\n"
                    "Download all videos?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.Yes,
                )
                if reply == QtWidgets.QMessageBox.No:
                    opts["no_playlist"] = True

        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(False)
        self.cancel_btn.show()
        self.close_btn.hide()
        self.status_label.setText("Starting download\u2026")
        self.playlist_status = ""

        self.worker = YTDLPWorker(url, opts)
        self.worker.progress.connect(self.on_progress)
        self.worker.status_update.connect(self.on_status_update)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def cancel_download(self):
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelling\u2026")

    def on_progress(self, value):
        self.progress_bar.setValue(value)
        if self.playlist_status:
            self.status_label.setText(
                f"{self.playlist_status} \u2014 {value}%"
            )
        else:
            self.status_label.setText(f"Downloading\u2026 {value}%")

    def on_status_update(self, text):
        self.playlist_status = text
        self.status_label.setText(text)

    def on_finished(self, ok, msg):
        self.download_btn.setEnabled(True)
        self.cancel_btn.hide()
        save_dir = self.save_dir_input.text().strip() or SAVE_DIR
        if ok:
            self.progress_bar.setValue(100)
            self.status_label.setText("Done.")
            QtWidgets.QMessageBox.information(
                self, "Success", f"Saved to:\n{save_dir}"
            )
        else:
            self.status_label.setText("Failed.")
            QtWidgets.QMessageBox.critical(
                self, "Error", f"yt-dlp failed.\n\nLast output:\n{msg}"
            )
        self.close_btn.show()


# --- Main entry ---
def main():
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseSoftwareOpenGL)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(NEON_STYLESHEET)
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
