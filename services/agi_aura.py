import sys
import time
import traceback
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen

# Runtime log (관측 가능성 확보)
LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "agi_aura_runtime.log"


def _log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass

# Aura Colors
COLOR_SURVIVAL = "#FF0000"
COLOR_ANXIETY  = "#FF4500"
COLOR_FOCUS    = "#FFD700"
COLOR_HARMONY  = "#00FF66"
COLOR_EXPRESS  = "#00BFFF"
COLOR_INSIGHT  = "#4B0082"
COLOR_EXPLORE  = "#9933FF"
COLOR_IDLE     = "#1A1A2E"

class CommandListener(QThread):
    command_received = pyqtSignal(str)
    def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line: break
                self.command_received.emit(line.strip())
            except: break

class AGIAura(QWidget):
    def __init__(self, initial_color='#00FFFF', thickness=0):
        super().__init__()
        
        _log(f"AGIAura init color={initial_color}")
        self.target_color = QColor(initial_color)
        self.current_color = QColor(initial_color)
        self.screen_rect = QApplication.primaryScreen().geometry()
        
        # Window Setup: Click-through, Always on Top, Frameless
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle("AGIAura")
        self.setGeometry(self.screen_rect)
        
        # Animation: Very slow (Low CPU)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100) # 10 FPS is enough for a slow color fade
        
        self.listener = CommandListener()
        self.listener.command_received.connect(self.handle_command)
        self.listener.start()

    def handle_command(self, cmd):
        if cmd.startswith("color:"):
            try: self.target_color = QColor(cmd.split(":")[1])
            except: pass
        elif cmd.startswith("state:"):
            try:
                state = cmd.split(":")[1].strip().lower()
                mapping = {
                    "explore": COLOR_EXPLORE, "anxiety": COLOR_ANXIETY,
                    "survival": COLOR_SURVIVAL, "focus": COLOR_FOCUS,
                    "express": COLOR_EXPRESS, "insight": COLOR_INSIGHT
                }
                self.target_color = QColor(mapping.get(state, COLOR_HARMONY))
            except: pass

    def animate(self):
        # Linear Interpolation for Color
        r = self.current_color.red()
        g = self.current_color.green()
        b = self.current_color.blue()
        tr, tg, tb = self.target_color.red(), self.target_color.green(), self.target_color.blue()
        
        step = 0.1
        self.current_color.setRed(int(r + (tr - r) * step))
        self.current_color.setGreen(int(g + (tg - g) * step))
        self.current_color.setBlue(int(b + (tb - b) * step))
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Minimalist: Just a border. No fills.
        w, h = self.width(), self.height()
        pen_width = 2 
        
        pen = QPen(self.current_color, pen_width)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw Rect
        painter.drawRect(pen_width//2, pen_width//2, w - pen_width, h - pen_width)

if __name__ == '__main__':
    app = None
    try:
        _log("main start")
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.aboutToQuit.connect(lambda: _log("aboutToQuit"))

        # liveness tick (5s)
        beat = QTimer()
        beat.timeout.connect(lambda: _log("alive"))
        beat.start(5000)

        c = sys.argv[1] if len(sys.argv) > 1 else "#00FFFF"
        aura = AGIAura(initial_color=c)
        aura.show()
        rc = app.exec_()
        _log(f"app.exec exit rc={rc}")
        sys.exit(rc)
    except Exception:
        _log("EXCEPTION:\n" + traceback.format_exc())
        raise
