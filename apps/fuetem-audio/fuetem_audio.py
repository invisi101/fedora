#!/usr/bin/env python3
"""Fuetem Audio — format conversion, trimming, and playback for audio files."""

import sys
import os
import json
import array
import subprocess
import tempfile
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

AUDIO_FORMATS = ["mp3", "flac", "opus", "wav", "aac", "m4a", "ogg"]
QUALITY_OPTIONS = ["best", "320K", "256K", "192K", "128K", "96K"]
AUDIO_EXTS = {".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac",
              ".wma", ".aiff", ".ape", ".mka"}
CONFIG_DIR = Path.home() / ".config" / "fuetem-audio"
RECENT_FILE = CONFIG_DIR / "recent.json"
MAX_RECENT = 10

NEON_STYLESHEET = """
QWidget#MainWindow {
    background: qlineargradient(y1:0, y2:1,
        stop:0 #0f0f23, stop:1 #12122e);
}
QLabel { color: #e0e0ff; }
QLabel#brandLarge {
    color: #f472b6;
    padding-top: 10px;
    padding-bottom: 10px;
}
QFrame#menuBar { background: transparent; }
QLabel#sectionLabel {
    color: #f472b6;
    font-weight: 600;
    font-size: 18px;
    letter-spacing: 0.5px;
}
QLabel#statusLabel { color: #a5b4fc; font-size: 18px; }
QLabel#timeLabel   { color: #c4c4f0; font-size: 16px; font-family: monospace; }
QLabel#fileInfoLabel { color: rgba(196,196,240,0.6); font-size: 15px; }

QLineEdit {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 8px;
    color: #e0e0ff;
    padding: 8px 12px;
    font-size: 18px;
    selection-background-color: #818cf8;
}
QLineEdit:focus { border: 1px solid #818cf8; }
QLineEdit::placeholder { color: rgba(196,196,240,0.35); }

QComboBox {
    background-color: #16213e;
    border: 1px solid #2d2d5e;
    border-radius: 8px;
    color: #e0e0ff;
    padding: 6px 12px;
    font-size: 18px;
    min-width: 90px;
}
QComboBox:focus, QComboBox:hover { border: 1px solid #818cf8; }
QComboBox::drop-down { border: none; padding-right: 8px; }
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
    selection-background-color: rgba(129,140,248,0.3);
    selection-color: #e0e0ff;
    outline: none;
}

QCheckBox { color: #c4c4f0; spacing: 6px; font-size: 16px; }
QCheckBox::indicator {
    width: 20px; height: 20px;
    border-radius: 4px;
    border: 2px solid #2d2d5e;
    background-color: #16213e;
}
QCheckBox::indicator:checked {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    border: 2px solid #818cf8;
}
QCheckBox::indicator:hover { border-color: #818cf8; }

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #0f0f23; width: 10px; border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: rgba(129,140,248,0.3); border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: rgba(129,140,248,0.5); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QProgressBar {
    background-color: #1a1a2e;
    border: 1px solid #2d2d5e;
    border-radius: 10px;
    min-height: 20px; max-height: 20px;
    text-align: center;
    color: #e0e0ff; font-weight: bold; font-size: 16px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, x2:1,
        stop:0 #34d399, stop:0.5 #06b6d4, stop:1 #818cf8);
    border-radius: 9px;
}

QPushButton#actionBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #f472b6, stop:1 #818cf8);
    color: #ffffff; border: none; border-radius: 8px;
    padding: 10px 26px; font-size: 18px; font-weight: 600;
}
QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #f9a8d4, stop:1 #a5b4fc);
}
QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #ec4899, stop:1 #6366f1);
}
QPushButton#actionBtn:disabled {
    background: #2d2d5e; color: rgba(196,196,240,0.4);
}

QPushButton#cancelBtn {
    background-color: transparent; color: #f472b6;
    border: 1px solid rgba(244,114,182,0.3); border-radius: 8px;
    padding: 10px 22px; font-size: 18px; font-weight: 500;
}
QPushButton#cancelBtn:hover {
    border-color: rgba(244,114,182,0.6);
    background-color: rgba(244,114,182,0.1);
}

QPushButton#openBtn {
    background-color: transparent; color: #06b6d4;
    border: 1px solid rgba(6,182,212,0.3); border-radius: 8px;
    padding: 8px 18px; font-size: 18px; font-weight: 500;
}
QPushButton#openBtn:hover {
    border-color: rgba(6,182,212,0.6);
    background-color: rgba(6,182,212,0.1);
}

QPushButton#transportBtn {
    background-color: #1a1a2e; color: #e0e0ff;
    border: 1px solid rgba(129,140,248,0.3);
    border-radius: 22px; font-size: 20px; font-weight: bold;
}
QPushButton#transportBtn:hover {
    border-color: rgba(129,140,248,0.7);
    background-color: rgba(129,140,248,0.1);
}
QPushButton#transportBtn:pressed { background-color: rgba(129,140,248,0.2); }
QPushButton#transportBtn:disabled {
    color: rgba(196,196,240,0.3); border-color: rgba(129,140,248,0.1);
}

QPushButton#recordBtn {
    background-color: #1a1a2e; color: #f87171;
    border: 1px solid rgba(248,113,113,0.3);
    border-radius: 22px; font-size: 20px; font-weight: bold;
}
QPushButton#recordBtn:hover {
    border-color: rgba(248,113,113,0.7);
    background-color: rgba(248,113,113,0.1);
}
QPushButton#recordBtn[recording="true"] {
    background-color: rgba(248,113,113,0.2);
    border-color: #f87171; color: #fca5a5;
}

QPushButton#loopBtn {
    background-color: transparent; color: #818cf8;
    border: 1px solid rgba(129,140,248,0.3); border-radius: 8px;
    padding: 6px 14px; font-size: 15px;
}
QPushButton#loopBtn:hover {
    border-color: rgba(129,140,248,0.6);
    background-color: rgba(129,140,248,0.1);
}
QPushButton#loopBtn:checked {
    background-color: rgba(129,140,248,0.2);
    border-color: #818cf8; color: #a5b4fc;
}

QPushButton#nudgeBtn {
    background-color: #16213e; color: #818cf8;
    border: 1px solid #2d2d5e; border-radius: 4px;
    font-size: 16px; font-weight: bold; padding: 0px;
}
QPushButton#nudgeBtn:hover {
    border-color: rgba(129,140,248,0.6);
    background-color: rgba(129,140,248,0.1);
}
QPushButton#nudgeBtn:pressed { background-color: rgba(129,140,248,0.2); }

QPushButton#setTimeBtn {
    background-color: transparent; color: #818cf8;
    border: 1px solid rgba(129,140,248,0.3); border-radius: 6px;
    padding: 4px 10px; font-size: 14px;
}
QPushButton#setTimeBtn:hover {
    border-color: rgba(129,140,248,0.7);
    background-color: rgba(129,140,248,0.1);
}

QPushButton#recentBtn {
    background-color: transparent; color: #a5b4fc;
    border: 1px solid rgba(129,140,248,0.2); border-radius: 6px;
    padding: 6px 14px; font-size: 15px;
}
QPushButton#recentBtn:hover {
    border-color: rgba(129,140,248,0.5);
    background-color: rgba(129,140,248,0.08);
}

QFrame#card {
    background-color: #1a1a2e;
    border: 1px solid rgba(129,140,248,0.15);
    border-radius: 12px;
}
QFrame#separator {
    background-color: rgba(129,140,248,0.12);
    max-height: 1px;
}

QMessageBox { background-color: #1a1a2e; }
QMessageBox QLabel { color: #e0e0ff; font-size: 14px; }
QMessageBox QPushButton {
    background-color: #2d2d5e; color: #e0e0ff;
    border: 1px solid rgba(129,140,248,0.3);
    border-radius: 6px; padding: 6px 20px; font-size: 14px;
}
QMessageBox QPushButton:hover {
    background-color: rgba(129,140,248,0.2); border-color: #818cf8;
}
"""


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _ms_to_hms(ms: int) -> str:
    h, rem = divmod(ms // 1000, 3600)
    m, s = divmod(rem, 60)
    frac = (ms % 1000) // 10
    return f"{h}:{m:02d}:{s:02d}.{frac:02d}"


def _secs_to_timestr(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _timestr_to_secs(text: str) -> float:
    text = text.strip()
    parts = text.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except Exception:
        raise ValueError(f"Invalid time format: '{text}'. Use HH:MM:SS.mmm")


def _build_ffmpeg_cmd(input_path, output_path, fmt, quality,
                      start=0.0, duration=0.0, normalize=False):
    cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats"]
    if start > 0:
        cmd.extend(["-ss", f"{start:.6f}"])
    cmd.extend(["-i", input_path])
    if duration > 0:
        cmd.extend(["-t", f"{duration:.6f}"])

    if fmt == "mp3":
        if quality == "best":
            cmd.extend(["-codec:a", "libmp3lame", "-q:a", "0"])
        else:
            cmd.extend(["-codec:a", "libmp3lame", "-b:a", quality.lower()])
    elif fmt == "flac":
        cmd.extend(["-codec:a", "flac"])
    elif fmt == "wav":
        cmd.extend(["-codec:a", "pcm_s16le"])
    elif fmt == "opus":
        br = quality.lower() if quality != "best" else "320k"
        cmd.extend(["-codec:a", "libopus", "-b:a", br])
    elif fmt in ("aac", "m4a"):
        br = quality.lower() if quality != "best" else "256k"
        cmd.extend(["-codec:a", "aac", "-b:a", br])
    elif fmt == "ogg":
        qmap = {"best": "10", "320K": "8", "256K": "7",
                "192K": "6", "128K": "4", "96K": "3"}
        cmd.extend(["-codec:a", "libvorbis", "-q:a", qmap.get(quality, "10")])

    if normalize:
        cmd.extend(["-af", "loudnorm"])

    cmd.append(output_path)
    return cmd


def _load_recent() -> list:
    try:
        return json.loads(RECENT_FILE.read_text())
    except Exception:
        return []


def _save_recent(paths: list):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RECENT_FILE.write_text(json.dumps(paths))


def _add_to_recent(path: str):
    paths = [p for p in _load_recent() if p != path]
    paths.insert(0, path)
    _save_recent(paths[:MAX_RECENT])


# ---------------------------------------------------------------------------
# Waveform worker
# ---------------------------------------------------------------------------

class WaveformWorker(QtCore.QThread):
    waveform_ready = QtCore.pyqtSignal(list)

    _RATE = 2000
    _BUCKETS = 2000

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def run(self):
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", self.path,
                 "-f", "s16le", "-ac", "1", "-ar", str(self._RATE), "-"],
                capture_output=True, timeout=120,
            )
            raw = result.stdout
            if len(raw) < 2:
                self.waveform_ready.emit([])
                return

            samples = array.array("h")
            samples.frombytes(raw[:len(raw) - len(raw) % 2])

            n = len(samples)
            if n == 0:
                self.waveform_ready.emit([])
                return

            max_val = max(abs(s) for s in samples) or 1
            buckets = []
            for i in range(self._BUCKETS):
                lo = i * n // self._BUCKETS
                hi = (i + 1) * n // self._BUCKETS
                chunk = samples[lo:hi]
                peak = max(abs(s) for s in chunk) if chunk else 0
                buckets.append(peak / max_val)

            self.waveform_ready.emit(buckets)
        except Exception:
            self.waveform_ready.emit([])


# ---------------------------------------------------------------------------
# Waveform widget
# ---------------------------------------------------------------------------

class WaveformWidget(QtWidgets.QWidget):
    seek_requested = QtCore.pyqtSignal(float)   # 0.0 – 1.0

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(90)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._samples: list = []
        self._loading = False
        self._position = 0.0
        self._trim_start = 0.0
        self._trim_end = 1.0
        self._pixmap: QtGui.QPixmap | None = None

    # -- public API --

    def set_loading(self, loading: bool):
        self._loading = loading
        if loading:
            self._samples = []
            self._pixmap = None
        self.update()

    def set_waveform(self, samples: list):
        self._samples = samples
        self._loading = False
        self._rebuild_pixmap()
        self.update()

    def set_position(self, ratio: float):
        self._position = max(0.0, min(1.0, ratio))
        self.update()

    def set_trim(self, start: float, end: float):
        self._trim_start = max(0.0, min(1.0, start))
        self._trim_end = max(0.0, min(1.0, end))
        self.update()

    # -- painting --

    def _rebuild_pixmap(self):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0 or not self._samples:
            self._pixmap = None
            return

        pm = QtGui.QPixmap(w, h)
        pm.fill(QtGui.QColor(22, 33, 62))
        p = QtGui.QPainter(pm)
        mid = h / 2
        n = len(self._samples)

        # Centre line
        p.setPen(QtGui.QPen(QtGui.QColor(45, 45, 94, 90), 1))
        p.drawLine(0, int(mid), w, int(mid))

        # Waveform bars with gradient
        grad = QtGui.QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, QtGui.QColor(244, 114, 182))
        grad.setColorAt(1.0, QtGui.QColor(129, 140, 248))
        p.setPen(QtGui.QPen(QtGui.QBrush(grad), 1))
        for i, amp in enumerate(self._samples):
            x = int(i * w / n)
            bar_h = max(1, int(amp * (mid - 4)))
            p.drawLine(x, int(mid - bar_h), x, int(mid + bar_h))

        p.end()
        self._pixmap = pm

    def resizeEvent(self, event):
        self._rebuild_pixmap()
        super().resizeEvent(event)

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        w, h = self.width(), self.height()

        if self._pixmap:
            p.drawPixmap(0, 0, self._pixmap)
        else:
            p.fillRect(0, 0, w, h, QtGui.QColor(22, 33, 62))
            p.setPen(QtGui.QColor(129, 140, 248, self._loading and 120 or 60))
            msg = "Loading waveform…" if self._loading else "Open a file to see waveform"
            p.drawText(QtCore.QRect(0, 0, w, h), QtCore.Qt.AlignCenter, msg)

        # Trim region
        if self._pixmap and self._trim_end > self._trim_start:
            x1 = int(self._trim_start * w)
            x2 = int(self._trim_end * w)
            p.fillRect(x1, 0, x2 - x1, h, QtGui.QColor(129, 140, 248, 38))
            p.setPen(QtGui.QPen(QtGui.QColor(129, 140, 248, 200), 1))
            p.drawLine(x1, 0, x1, h)
            p.drawLine(x2, 0, x2, h)

        # Playhead
        px = int(self._position * w)
        p.setPen(QtGui.QPen(QtGui.QColor(224, 224, 255, 210), 2))
        p.drawLine(px, 0, px, h)

        # Border
        p.setPen(QtGui.QPen(QtGui.QColor(45, 45, 94, 70), 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 4, 4)

    # -- mouse seek --

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.seek_requested.emit(event.x() / self.width())

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            ratio = max(0.0, min(1.0, event.x() / self.width()))
            self.seek_requested.emit(ratio)


# ---------------------------------------------------------------------------
# ffmpeg worker
# ---------------------------------------------------------------------------

class FFmpegWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, cmd: list, total_seconds: float = 0.0):
        super().__init__()
        self.cmd = cmd
        self.total_seconds = total_seconds
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

    def run(self):
        try:
            self._process = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError as e:
            self.finished.emit(False, str(e))
            return

        last_line = ""
        for line in (self._process.stdout or []):
            if self._cancelled:
                break
            line = line.rstrip()
            last_line = line
            if line.startswith("out_time_ms=") and self.total_seconds > 0:
                try:
                    us = int(line.split("=", 1)[1])
                    pct = min(100, int(us / (self.total_seconds * 1_000_000) * 100))
                    self.progress.emit(pct)
                except (ValueError, ZeroDivisionError):
                    pass

        ret = self._process.wait()
        if self._cancelled:
            self.finished.emit(False, "Cancelled.")
        else:
            self.finished.emit(ret == 0, last_line)


# ---------------------------------------------------------------------------
# Split worker — two stream-copy commands run sequentially
# ---------------------------------------------------------------------------

class SplitWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, cmd1: list, cmd2: list):
        super().__init__()
        self.cmd1 = cmd1
        self.cmd2 = cmd2

    def run(self):
        for i, cmd in enumerate([self.cmd1, self.cmd2], 1):
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode != 0:
                self.finished.emit(False, f"Part {i} failed")
                return
        self.finished.emit(True, "Split complete.")


# ---------------------------------------------------------------------------
# Record worker
# ---------------------------------------------------------------------------

class RecordWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, output_path: str):
        super().__init__()
        self.output_path = output_path
        self._process = None

    def stop_recording(self):
        if self._process:
            self._process.terminate()

    def run(self):
        cmd = ["ffmpeg", "-y", "-f", "pulse", "-i", "default", self.output_path]
        try:
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self._process.wait()
            ok = self._process.returncode in (0, -15)
            self.finished.emit(ok, self.output_path)
        except FileNotFoundError as e:
            self.finished.emit(False, str(e))


# ---------------------------------------------------------------------------
# Time spin widget  (label + [−] lineEdit [+])
# ---------------------------------------------------------------------------

class TimeSpinWidget(QtWidgets.QWidget):
    STEP_MS = 100

    def __init__(self, label: str):
        super().__init__()
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        lay.addWidget(QtWidgets.QLabel(label))

        self._minus = QtWidgets.QPushButton("−")
        self._minus.setObjectName("nudgeBtn")
        self._minus.setFixedSize(28, 34)
        self._minus.setCursor(QtCore.Qt.PointingHandCursor)
        self._minus.clicked.connect(self._nudge_minus)
        lay.addWidget(self._minus)

        self._edit = QtWidgets.QLineEdit("00:00:00.000")
        self._edit.setFixedWidth(148)
        self._edit.setPlaceholderText("HH:MM:SS.mmm")
        lay.addWidget(self._edit)

        self._plus = QtWidgets.QPushButton("+")
        self._plus.setObjectName("nudgeBtn")
        self._plus.setFixedSize(28, 34)
        self._plus.setCursor(QtCore.Qt.PointingHandCursor)
        self._plus.clicked.connect(self._nudge_plus)
        lay.addWidget(self._plus)

    # proxy the inner line-edit
    def text(self) -> str:
        return self._edit.text()

    def setText(self, t: str):
        self._edit.setText(t)

    @property
    def textChanged(self):
        return self._edit.textChanged

    def _nudge(self, delta_ms: int):
        try:
            secs = _timestr_to_secs(self._edit.text())
            secs = max(0.0, secs + delta_ms / 1000)
            self._edit.setText(_secs_to_timestr(secs))
        except ValueError:
            pass

    def _nudge_minus(self):
        self._nudge(-self.STEP_MS)

    def _nudge_plus(self):
        self._nudge(self.STEP_MS)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Fuetem Audio")
        self.setMinimumSize(820, 680)
        self.setAcceptDrops(True)

        self.current_file: str | None = None
        self.is_slider_dragging = False
        self.is_recording = False
        self.ffmpeg_worker: FFmpegWorker | None = None
        self.split_worker: SplitWorker | None = None
        self.record_worker: RecordWorker | None = None
        self.waveform_worker: WaveformWorker | None = None
        self._ffmpeg_done_cb = None

        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.error.connect(self._on_player_error)

        self._build_ui()
        self._refresh_controls()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _make_card(self, title=""):
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

    def _transport_btn(self, text: str) -> QtWidgets.QPushButton:
        b = QtWidgets.QPushButton(text)
        b.setObjectName("transportBtn")
        b.setFixedSize(44, 44)
        b.setCursor(QtCore.Qt.PointingHandCursor)
        return b

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        body = QtWidgets.QWidget()
        bl = QtWidgets.QVBoxLayout(body)
        bl.setContentsMargins(24, 12, 24, 20)
        bl.setSpacing(12)
        bl.addWidget(self._build_file_card())
        bl.addWidget(self._build_preview_card())
        bl.addWidget(self._build_trim_card())
        bl.addWidget(self._build_convert_card())
        bl.addWidget(self._build_metadata_card())
        bl.addWidget(self._build_status_card())
        bl.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _build_header(self):
        bar = QtWidgets.QFrame()
        bar.setObjectName("menuBar")
        bar.setMinimumHeight(64)
        lay = QtWidgets.QHBoxLayout(bar)
        lay.setContentsMargins(29, 0, 24, 0)

        lbl = QtWidgets.QLabel("Fuetem Audio")
        lbl.setObjectName("brandLarge")
        font = QtGui.QFont("Vegan Style Personal Use")
        font.setPixelSize(36)
        font.setBold(True)
        lbl.setFont(font)
        lbl.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        lay.addWidget(lbl)
        lay.addStretch(1)

        self.recent_btn = QtWidgets.QPushButton("Recent ▾")
        self.recent_btn.setObjectName("recentBtn")
        self.recent_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.recent_btn.clicked.connect(self._show_recent_menu)
        lay.addWidget(self.recent_btn, alignment=QtCore.Qt.AlignVCenter)
        return bar

    def _build_file_card(self):
        card, lay = self._make_card("FILE")
        row = QtWidgets.QHBoxLayout()

        open_btn = QtWidgets.QPushButton("Open File…")
        open_btn.setObjectName("openBtn")
        open_btn.setCursor(QtCore.Qt.PointingHandCursor)
        open_btn.clicked.connect(self._open_file)
        row.addWidget(open_btn)

        self.file_name_label = QtWidgets.QLabel("No file loaded")
        self.file_name_label.setObjectName("statusLabel")
        self.file_name_label.setWordWrap(True)
        row.addWidget(self.file_name_label, 1)
        lay.addLayout(row)

        self.file_info_label = QtWidgets.QLabel("")
        self.file_info_label.setObjectName("fileInfoLabel")
        lay.addWidget(self.file_info_label)
        return card

    def _build_preview_card(self):
        card, lay = self._make_card("PREVIEW")

        # Transport row
        tr = QtWidgets.QHBoxLayout()
        tr.setSpacing(8)

        self.play_btn = self._transport_btn("▶")
        self.play_btn.clicked.connect(self._toggle_play)
        tr.addWidget(self.play_btn)

        self.stop_btn = self._transport_btn("■")
        self.stop_btn.clicked.connect(self._stop_playback)
        tr.addWidget(self.stop_btn)

        self.record_btn = QtWidgets.QPushButton("⏺")
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.setFixedSize(44, 44)
        self.record_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.record_btn.clicked.connect(self._toggle_record)
        tr.addWidget(self.record_btn)

        self.loop_btn = QtWidgets.QPushButton("⟳ Loop")
        self.loop_btn.setObjectName("loopBtn")
        self.loop_btn.setCheckable(True)
        self.loop_btn.setCursor(QtCore.Qt.PointingHandCursor)
        tr.addWidget(self.loop_btn)

        tr.addStretch(1)

        self.time_label = QtWidgets.QLabel("0:00:00.00 / 0:00:00.00")
        self.time_label.setObjectName("timeLabel")
        tr.addWidget(self.time_label)
        lay.addLayout(tr)

        # Waveform (doubles as seek control)
        self.waveform = WaveformWidget()
        self.waveform.seek_requested.connect(self._on_waveform_seek)
        lay.addWidget(self.waveform)
        return card

    def _build_trim_card(self):
        card, lay = self._make_card("TRIM")

        # Time inputs
        time_row = QtWidgets.QHBoxLayout()
        time_row.setSpacing(6)

        self.trim_start = TimeSpinWidget("Start:")
        time_row.addWidget(self.trim_start)
        set_s = QtWidgets.QPushButton("Set")
        set_s.setObjectName("setTimeBtn")
        set_s.setFixedWidth(44)
        set_s.setCursor(QtCore.Qt.PointingHandCursor)
        set_s.setToolTip("Set to current playback position")
        set_s.clicked.connect(lambda: self._set_time_from_position(self.trim_start))
        time_row.addWidget(set_s)

        time_row.addSpacing(14)

        self.trim_end = TimeSpinWidget("End:")
        time_row.addWidget(self.trim_end)
        set_e = QtWidgets.QPushButton("Set")
        set_e.setObjectName("setTimeBtn")
        set_e.setFixedWidth(44)
        set_e.setCursor(QtCore.Qt.PointingHandCursor)
        set_e.setToolTip("Set to current playback position")
        set_e.clicked.connect(lambda: self._set_time_from_position(self.trim_end))
        time_row.addWidget(set_e)

        time_row.addStretch(1)
        lay.addLayout(time_row)

        # Connect trim changes → waveform highlight
        self.trim_start.textChanged.connect(self._update_waveform_trim)
        self.trim_end.textChanged.connect(self._update_waveform_trim)

        # Format / quality / normalize / save
        save_row = QtWidgets.QHBoxLayout()
        save_row.setSpacing(8)
        save_row.addWidget(QtWidgets.QLabel("Format:"))
        self.trim_format = QtWidgets.QComboBox()
        self.trim_format.addItems(AUDIO_FORMATS)
        save_row.addWidget(self.trim_format)
        save_row.addSpacing(8)
        save_row.addWidget(QtWidgets.QLabel("Quality:"))
        self.trim_quality = QtWidgets.QComboBox()
        self.trim_quality.addItems(QUALITY_OPTIONS)
        save_row.addWidget(self.trim_quality)
        save_row.addSpacing(8)
        self.trim_normalize = QtWidgets.QCheckBox("Normalize")
        save_row.addWidget(self.trim_normalize)
        save_row.addStretch(1)
        self.save_trim_btn = QtWidgets.QPushButton("Save Trim")
        self.save_trim_btn.setObjectName("actionBtn")
        self.save_trim_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.save_trim_btn.clicked.connect(self._save_trim)
        save_row.addWidget(self.save_trim_btn)
        lay.addLayout(save_row)

        # Split row
        sep = QtWidgets.QFrame()
        sep.setObjectName("separator")
        lay.addWidget(sep)

        split_row = QtWidgets.QHBoxLayout()
        split_lbl = QtWidgets.QLabel("Split file at current playback position")
        split_lbl.setObjectName("fileInfoLabel")
        split_row.addWidget(split_lbl)
        split_row.addStretch(1)
        self.split_btn = QtWidgets.QPushButton("Split Here")
        self.split_btn.setObjectName("actionBtn")
        self.split_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.split_btn.clicked.connect(self._split_at_position)
        split_row.addWidget(self.split_btn)
        lay.addLayout(split_row)
        return card

    def _build_convert_card(self):
        card, lay = self._make_card("CONVERT")
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QtWidgets.QLabel("Format:"))
        self.conv_format = QtWidgets.QComboBox()
        self.conv_format.addItems(AUDIO_FORMATS)
        row.addWidget(self.conv_format)
        row.addSpacing(8)
        row.addWidget(QtWidgets.QLabel("Quality:"))
        self.conv_quality = QtWidgets.QComboBox()
        self.conv_quality.addItems(QUALITY_OPTIONS)
        row.addWidget(self.conv_quality)
        row.addSpacing(8)
        self.conv_normalize = QtWidgets.QCheckBox("Normalize")
        row.addWidget(self.conv_normalize)
        row.addStretch(1)
        self.convert_btn = QtWidgets.QPushButton("Convert")
        self.convert_btn.setObjectName("actionBtn")
        self.convert_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.convert_btn.clicked.connect(self._convert)
        row.addWidget(self.convert_btn)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._cancel_ffmpeg)
        self.cancel_btn.hide()
        row.addWidget(self.cancel_btn)
        lay.addLayout(row)
        return card

    def _build_metadata_card(self):
        card, lay = self._make_card("METADATA")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(8)

        self.meta_title  = QtWidgets.QLineEdit(); self.meta_title.setPlaceholderText("Title")
        self.meta_artist = QtWidgets.QLineEdit(); self.meta_artist.setPlaceholderText("Artist")
        self.meta_album  = QtWidgets.QLineEdit(); self.meta_album.setPlaceholderText("Album")
        self.meta_year   = QtWidgets.QLineEdit(); self.meta_year.setPlaceholderText("Year")

        grid.addWidget(QtWidgets.QLabel("Title:"),  0, 0)
        grid.addWidget(self.meta_title,             0, 1)
        grid.addWidget(QtWidgets.QLabel("Artist:"), 0, 2)
        grid.addWidget(self.meta_artist,            0, 3)
        grid.addWidget(QtWidgets.QLabel("Album:"),  1, 0)
        grid.addWidget(self.meta_album,             1, 1)
        grid.addWidget(QtWidgets.QLabel("Year:"),   1, 2)
        grid.addWidget(self.meta_year,              1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        lay.addLayout(grid)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.save_tags_btn = QtWidgets.QPushButton("Save Tags")
        self.save_tags_btn.setObjectName("actionBtn")
        self.save_tags_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.save_tags_btn.clicked.connect(self._save_metadata)
        btn_row.addWidget(self.save_tags_btn)
        lay.addLayout(btn_row)
        return card

    def _build_status_card(self):
        card, lay = self._make_card()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setValue(0)
        lay.addWidget(self.progress_bar)
        self.status_label = QtWidgets.QLabel("Idle.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(self.status_label)
        return card

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------

    def _open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Audio File", str(Path.home()),
            "Audio Files (*.mp3 *.flac *.wav *.ogg *.opus *.m4a *.aac "
            "*.wma *.aiff *.ape *.mka);;All Files (*)",
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        self.current_file = path
        self.file_name_label.setText(os.path.basename(path))
        self._probe_file(path)
        self._load_metadata_fields(path)
        self.player.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(path)))
        _add_to_recent(path)
        self._start_waveform(path)
        self._refresh_controls()

    def _probe_file(self, path: str):
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format=duration,bit_rate:"
                 "stream=codec_name,sample_rate,channels",
                 "-of", "json", path],
                capture_output=True, text=True, timeout=10,
            )
            info = json.loads(r.stdout)
        except Exception:
            self.file_info_label.setText("")
            return

        parts = []
        streams = info.get("streams", [])
        fmt = info.get("format", {})

        if streams:
            s = streams[0]
            if s.get("codec_name"):
                parts.append(f"Codec: {s['codec_name']}")
            if s.get("sample_rate"):
                parts.append(f"SR: {s['sample_rate']} Hz")
            if s.get("channels"):
                parts.append("Stereo" if str(s["channels"]) == "2"
                             else f"Ch: {s['channels']}")

        if fmt.get("duration"):
            try:
                dur = float(fmt["duration"])
                h, rem = divmod(int(dur), 3600)
                m, s2 = divmod(rem, 60)
                parts.insert(0, f"Duration: {h}:{m:02d}:{s2:02d}")
                self.trim_end.setText(_secs_to_timestr(dur))
                self.trim_start.setText("00:00:00.000")
            except ValueError:
                pass

        if fmt.get("bit_rate"):
            try:
                parts.append(f"Bitrate: {int(fmt['bit_rate']) // 1000} kbps")
            except ValueError:
                pass

        self.file_info_label.setText("  |  ".join(parts))

    def _start_waveform(self, path: str):
        if self.waveform_worker and self.waveform_worker.isRunning():
            self.waveform_worker.terminate()
        self.waveform.set_loading(True)
        self.waveform_worker = WaveformWorker(path)
        self.waveform_worker.waveform_ready.connect(self._on_waveform_ready)
        self.waveform_worker.start()

    def _on_waveform_ready(self, samples: list):
        self.waveform.set_waveform(samples)
        self._update_waveform_trim()

    # ------------------------------------------------------------------
    # Recent files
    # ------------------------------------------------------------------

    def _show_recent_menu(self):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:#1a1a2e; color:#e0e0ff; border:1px solid #2d2d5e; }"
            "QMenu::item:selected { background:rgba(129,140,248,0.25); }"
            "QMenu::item { padding:6px 20px; font-size:15px; }"
        )
        recent = [p for p in _load_recent() if os.path.exists(p)]
        if not recent:
            action = menu.addAction("No recent files")
            action.setEnabled(False)
        else:
            for path in recent:
                action = menu.addAction(os.path.basename(path))
                action.setToolTip(path)
                action.triggered.connect(lambda _checked, p=path: self._load_file(p))
        menu.exec_(self.recent_btn.mapToGlobal(
            QtCore.QPoint(0, self.recent_btn.height())))

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in AUDIO_EXTS:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in AUDIO_EXTS:
                self._load_file(path)
                break

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _stop_playback(self):
        self.player.stop()

    def _on_waveform_seek(self, ratio: float):
        dur = self.player.duration()
        if dur > 0:
            self.player.setPosition(int(ratio * dur))

    def _on_state_changed(self, state):
        playing = state == QMediaPlayer.PlayingState
        self.play_btn.setText("⏸" if playing else "▶")
        self.stop_btn.setEnabled(state != QMediaPlayer.StoppedState)

    def _on_position_changed(self, pos_ms: int):
        # Loop check
        if self.loop_btn.isChecked() and self.current_file:
            try:
                end_ms = int(_timestr_to_secs(self.trim_end.text()) * 1000)
                start_ms = int(_timestr_to_secs(self.trim_start.text()) * 1000)
                if pos_ms >= end_ms > start_ms:
                    self.player.setPosition(start_ms)
                    return
            except ValueError:
                pass

        dur_ms = self.player.duration()
        self.time_label.setText(f"{_ms_to_hms(pos_ms)} / {_ms_to_hms(dur_ms)}")
        if dur_ms > 0:
            self.waveform.set_position(pos_ms / dur_ms)

    def _on_duration_changed(self, dur_ms: int):
        if dur_ms > 0:
            self.trim_end.setText(_secs_to_timestr(dur_ms / 1000))

    def _on_player_error(self, error):
        if error != QMediaPlayer.NoError:
            self.status_label.setText(f"Playback error: {self.player.errorString()}")

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _toggle_record(self):
        if self.is_recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Recording",
            str(Path.home() / "Music" / "recording.wav"),
            "WAV (*.wav);;MP3 (*.mp3);;FLAC (*.flac);;OGG (*.ogg)",
        )
        if not path:
            return
        self.is_recording = True
        self.record_btn.setProperty("recording", "true")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.record_btn.setText("⏹")
        self.status_label.setText("Recording…")
        self.record_worker = RecordWorker(path)
        self.record_worker.finished.connect(self._on_record_finished)
        self.record_worker.start()

    def _stop_record(self):
        if self.record_worker:
            self.record_worker.stop_recording()
        self._reset_record_btn()

    def _reset_record_btn(self):
        self.is_recording = False
        self.record_btn.setProperty("recording", "false")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.record_btn.setText("⏺")

    def _on_record_finished(self, ok: bool, path: str):
        self._reset_record_btn()
        if ok:
            self.status_label.setText(f"Saved: {os.path.basename(path)}")
            if QtWidgets.QMessageBox.question(
                self, "Recording Saved",
                f"Saved to:\n{path}\n\nLoad this file now?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            ) == QtWidgets.QMessageBox.Yes:
                self._load_file(path)
        else:
            self.status_label.setText(f"Recording failed: {path}")

    # ------------------------------------------------------------------
    # Trim
    # ------------------------------------------------------------------

    def _set_time_from_position(self, target: TimeSpinWidget):
        target.setText(_secs_to_timestr(self.player.position() / 1000))

    def _update_waveform_trim(self):
        dur = self.player.duration()
        if dur <= 0:
            return
        try:
            s = _timestr_to_secs(self.trim_start.text()) * 1000 / dur
            e = _timestr_to_secs(self.trim_end.text()) * 1000 / dur
            self.waveform.set_trim(s, e)
        except ValueError:
            pass

    def _save_trim(self):
        if not self.current_file:
            QtWidgets.QMessageBox.warning(self, "No File", "Open an audio file first.")
            return
        try:
            start_s = _timestr_to_secs(self.trim_start.text())
            end_s   = _timestr_to_secs(self.trim_end.text())
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Invalid Time", str(e))
            return
        if end_s <= start_s:
            QtWidgets.QMessageBox.warning(self, "Invalid Range",
                                          "End time must be after start time.")
            return

        fmt = self.trim_format.currentText()
        src = Path(self.current_file)
        tag = self.trim_start.text().replace(":", "-").replace(".", "_")
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Trimmed File",
            str(src.parent / f"{src.stem}_trim_{tag}.{fmt}"),
            f"{fmt.upper()} (*.{fmt});;All Files (*)",
        )
        if not out_path:
            return

        duration_s = end_s - start_s
        cmd = _build_ffmpeg_cmd(
            self.current_file, out_path, fmt,
            self.trim_quality.currentText(),
            start=start_s, duration=duration_s,
            normalize=self.trim_normalize.isChecked(),
        )
        self._run_ffmpeg(cmd, duration_s, f"Trimming to {fmt.upper()}…")

    # ------------------------------------------------------------------
    # Split
    # ------------------------------------------------------------------

    def _split_at_position(self):
        if not self.current_file:
            QtWidgets.QMessageBox.warning(self, "No File", "Open an audio file first.")
            return
        pos_ms = self.player.position()
        pos_s  = pos_ms / 1000
        if pos_s <= 0:
            QtWidgets.QMessageBox.warning(self, "No Position",
                                          "Seek to a position before splitting.")
            return

        src = Path(self.current_file)
        ext = src.suffix
        out_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose Output Folder", str(src.parent))
        if not out_dir:
            return

        part1 = str(Path(out_dir) / f"{src.stem}_part1{ext}")
        part2 = str(Path(out_dir) / f"{src.stem}_part2{ext}")
        dur_ms = self.player.duration()

        if QtWidgets.QMessageBox.question(
            self, "Split File",
            f"Split at {_ms_to_hms(pos_ms)}\n\n"
            f"Part 1: {src.stem}_part1{ext}  (0 → {_ms_to_hms(pos_ms)})\n"
            f"Part 2: {src.stem}_part2{ext}  ({_ms_to_hms(pos_ms)} → {_ms_to_hms(dur_ms)})\n\n"
            "Proceed?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        ) != QtWidgets.QMessageBox.Yes:
            return

        cmd1 = ["ffmpeg", "-y", "-i", self.current_file,
                "-t", f"{pos_s:.6f}", "-codec", "copy", part1]
        cmd2 = ["ffmpeg", "-y", "-ss", f"{pos_s:.6f}",
                "-i", self.current_file, "-codec", "copy", part2]

        self._set_busy(True)
        self.status_label.setText("Splitting…")
        self.progress_bar.setValue(0)
        self.split_worker = SplitWorker(cmd1, cmd2)
        self.split_worker.finished.connect(self._on_split_done)
        self.split_worker.start()

    def _on_split_done(self, ok: bool, msg: str):
        self._set_busy(False)
        if ok:
            self.progress_bar.setValue(100)
            self.status_label.setText("Split complete.")
        else:
            self.status_label.setText(f"Split failed: {msg}")

    # ------------------------------------------------------------------
    # Convert
    # ------------------------------------------------------------------

    def _convert(self):
        if not self.current_file:
            QtWidgets.QMessageBox.warning(self, "No File", "Open an audio file first.")
            return
        fmt = self.conv_format.currentText()
        src = Path(self.current_file)
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Converted File",
            str(src.parent / f"{src.stem}.{fmt}"),
            f"{fmt.upper()} (*.{fmt});;All Files (*)",
        )
        if not out_path:
            return
        dur_s = self.player.duration() / 1000
        cmd = _build_ffmpeg_cmd(
            self.current_file, out_path, fmt,
            self.conv_quality.currentText(),
            normalize=self.conv_normalize.isChecked(),
        )
        self._run_ffmpeg(cmd, dur_s, f"Converting to {fmt.upper()}…")

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _load_metadata_fields(self, path: str):
        for w in (self.meta_title, self.meta_artist, self.meta_album, self.meta_year):
            w.clear()
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format_tags=title,artist,album,date",
                 "-of", "json", path],
                capture_output=True, text=True, timeout=10,
            )
            tags = json.loads(r.stdout).get("format", {}).get("tags", {})
        except Exception:
            return
        self.meta_title.setText(tags.get("title", ""))
        self.meta_artist.setText(tags.get("artist", ""))
        self.meta_album.setText(tags.get("album", ""))
        self.meta_year.setText(tags.get("date", ""))

    def _save_metadata(self):
        if not self.current_file:
            QtWidgets.QMessageBox.warning(self, "No File", "Open an audio file first.")
            return

        src = Path(self.current_file)
        fd, tmp = tempfile.mkstemp(suffix=src.suffix, dir=str(src.parent))
        os.close(fd)

        cmd = ["ffmpeg", "-y", "-i", self.current_file,
               "-metadata", f"title={self.meta_title.text()}",
               "-metadata", f"artist={self.meta_artist.text()}",
               "-metadata", f"album={self.meta_album.text()}",
               "-metadata", f"date={self.meta_year.text()}",
               "-codec", "copy", tmp]

        was_playing = self.player.state() == QMediaPlayer.PlayingState
        self.player.stop()

        def on_done():
            try:
                os.replace(tmp, self.current_file)
            except OSError as e:
                self.status_label.setText(f"Failed to save tags: {e}")
                return
            self.status_label.setText("Tags saved.")
            if was_playing:
                self.player.play()

        self._run_ffmpeg(cmd, 0, "Saving tags…", on_done=on_done)

    # ------------------------------------------------------------------
    # ffmpeg runner
    # ------------------------------------------------------------------

    def _run_ffmpeg(self, cmd: list, total_secs: float, status_msg: str,
                    on_done=None):
        self._set_busy(True)
        self.status_label.setText(status_msg)
        self.progress_bar.setValue(0)
        self._ffmpeg_done_cb = on_done

        self.ffmpeg_worker = FFmpegWorker(cmd, total_secs)
        self.ffmpeg_worker.progress.connect(self.progress_bar.setValue)
        self.ffmpeg_worker.finished.connect(self._on_ffmpeg_done)
        self.ffmpeg_worker.start()

    def _cancel_ffmpeg(self):
        if self.ffmpeg_worker:
            self.ffmpeg_worker.cancel()
        self.status_label.setText("Cancelling…")

    def _on_ffmpeg_done(self, ok: bool, msg: str):
        self._set_busy(False)
        if ok:
            self.progress_bar.setValue(100)
            self.status_label.setText("Done.")
            if self._ffmpeg_done_cb:
                self._ffmpeg_done_cb()
        else:
            self.status_label.setText(
                f"Failed: {msg[-100:] if msg else 'unknown error'}")
        self._ffmpeg_done_cb = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool):
        for btn in (self.save_trim_btn, self.split_btn,
                    self.convert_btn, self.save_tags_btn):
            btn.setEnabled(not busy)
        self.cancel_btn.setVisible(busy)

    def _refresh_controls(self):
        has = self.current_file is not None
        for btn in (self.play_btn, self.stop_btn, self.save_trim_btn,
                    self.split_btn, self.convert_btn, self.save_tags_btn):
            btn.setEnabled(has)

    def closeEvent(self, event):
        if self.is_recording:
            self._stop_record()
        self.player.stop()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
