import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient

class CommandListener(QThread):
    command_received = pyqtSignal(str)

    def run(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                self.command_received.emit(line.strip())
            except:
                break

class AGIAura(QWidget):
    def __init__(self, initial_color='#00FFFF', thickness=200): # 200px로 더 넓게
        super().__init__()
        
        self.target_color_hex = initial_color
        self.current_color = QColor(initial_color)
        self.thickness = thickness
        self.screen_rect = QApplication.primaryScreen().geometry()
        
        # 윈도우 설정
        self.setWindowFlags(
            Qt.FramelessWindowHint |        # 테두리 없음
            Qt.WindowStaysOnTopHint |       # 항상 위
            Qt.Tool |                       # 작업표시줄 숨김
            Qt.WindowTransparentForInput    # 클릭 통과 (중요!)
        )
        self.setAttribute(Qt.WA_TranslucentBackground) # 배경 투명
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 전체 화면
        self.setGeometry(self.screen_rect)
        
        # 애니메이션 타이머 (약 30 FPS로 부드럽게)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
        self.time_val = 0.0
        
        # 명령 리스너 시작
        self.listener = CommandListener()
        self.listener.command_received.connect(self.handle_command)
        self.listener.start()

    def handle_command(self, cmd):
        if cmd.startswith("color:"):
            hex_code = cmd.split(":")[1]
            self.target_color_hex = hex_code

    def animate(self):
        self.time_val += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        t = self.thickness
        
        # 호흡 효과 계산 (Brightness 변동)
        import math
        wave = (math.sin(self.time_val) + 1) / 2  # 0.0 ~ 1.0
        
        # 사용자 피드백: "오퍼시티를 조금 더 주어" -> 더 은은하게 (투명하게)
        # 30 ~ 150 (최대 60% 불투명도)
        alpha_base = 30 + int(wave * 120)
        
        base_color = QColor(self.target_color_hex)
        
        # 투명한 색 (끝부분)
        transparent_color = QColor(base_color)
        transparent_color.setAlpha(0)
        
        # 시작 색 (가장자리) - 호흡 적용
        start_color = QColor(base_color)
        start_color.setAlpha(alpha_base)
        
        # --- Gradient 4방향 그리기 ---
        
        # 1. Top
        grad_top = QLinearGradient(0, 0, 0, t)
        grad_top.setColorAt(0, start_color)
        grad_top.setColorAt(1, transparent_color)
        painter.fillRect(0, 0, w, t, grad_top)
        
        # 2. Bottom
        grad_bottom = QLinearGradient(0, h-t, 0, h)
        grad_bottom.setColorAt(0, transparent_color)
        grad_bottom.setColorAt(1, start_color)
        painter.fillRect(0, h-t, w, t, grad_bottom)
        
        # 3. Left
        grad_left = QLinearGradient(0, 0, t, 0)
        grad_left.setColorAt(0, start_color)
        grad_left.setColorAt(1, transparent_color)
        painter.fillRect(0, 0, t, h, grad_left)
        
        # 4. Right
        grad_right = QLinearGradient(w-t, 0, w, 0)
        grad_right.setColorAt(0, transparent_color)
        grad_right.setColorAt(1, start_color)
        painter.fillRect(w-t, 0, t, h, grad_right)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    color = sys.argv[1] if len(sys.argv) > 1 else "#00FFFF"
    aura = AGIAura(initial_color=color, thickness=150) # 두툼한 Inner Glow
    aura.show()
    
    sys.exit(app.exec_())
