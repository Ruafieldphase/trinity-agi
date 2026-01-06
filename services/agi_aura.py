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
COLOR_HUD_TEXT = "#00FFFF"
COLOR_HUD_BG   = "#000000"

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
        
        # HUD State
        self.hud_text = "AGI Systems Operational"
        self.hud_subtext = "Zone: IDLE"
        self.hud_opacity = 0.0
        self.target_hud_opacity = 0.0
        self.confidence = 0.0
        
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
        elif cmd.startswith("hud:"):
            try:
                parts = cmd.split(":", 1)[1].split("|")
                self.hud_text = parts[0].strip()
                if len(parts) > 1: self.hud_subtext = parts[1].strip()
                if len(parts) > 2: self.confidence = float(parts[2].strip())
                self.target_hud_opacity = 0.8
            except: pass
        elif cmd.startswith("hud_off"):
            self.target_hud_opacity = 0.0

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
        
        # HUD Opacity Fade
        self.hud_opacity += (self.target_hud_opacity - self.hud_opacity) * 0.1
        
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

        # Draw HUD (Phase 8: Aura v2)
        if self.hud_opacity > 0.05:
            self.draw_hud(painter)

    def draw_hud(self, painter):
        w, h = self.width(), self.height()
        hud_h = 60
        hud_w = 400
        
        # HUD Container
        painter.setOpacity(self.hud_opacity)
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect((w - hud_w)//2, h - hud_h - 40, hud_w, hud_h, 10, 10)
        
        # Text
        painter.setPen(QColor(COLOR_HUD_TEXT))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText((w - hud_w)//2 + 20, h - hud_h - 10, self.hud_text)
        
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText((w - hud_w)//2 + 20, h - hud_h + 10, self.hud_subtext)
        
        # Confidence Bar
        bar_w = 100
        bar_x = (w + hud_w)//2 - bar_w - 20
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRect(bar_x, h - hud_h - 5, bar_w, 10)
        
        painter.setBrush(QColor(0, 255, 255))
        painter.drawRect(bar_x, h - hud_h - 5, int(bar_w * self.confidence), 10)

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
