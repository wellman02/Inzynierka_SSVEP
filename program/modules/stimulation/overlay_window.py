import sys
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor
from config import STIMULI_MAP

class Stimulus:
    def __init__(self, name, rect, freq, color=Qt.white):
        self.name = name
        self.rect = rect
        self.freq = freq
        self.color = QColor(color)

class OverlayWindow(QMainWindow):
    def __init__(self, cmd_queue):
        super().__init__()
        self.frame_counter = 0
        self.refresh_rate = 60 
        
        screen = QDesktopWidget().screenGeometry()
        self.width = screen.width()
        self.height = screen.height()
        
        self.stimuli = self.setup_dynamic_stimuli()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

        # Timer ustawiony na 1ms, ale faktyczne odświeżanie 
        # wymuszamy przez systemowy zegar klatek
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_screen)
        # 16ms to około 60Hz, ale lepiej dać 15ms by "doganiać" monitor
        self.timer.start(15) 

    def setup_dynamic_stimuli(self):
        freq_by_cmd = {v: k for k, v in STIMULI_MAP.items()}
        size = 180 
        margin = 60
        
        pos = {
            "UP":    QRect((self.width - size) // 2, margin, size, size),
            "DOWN":  QRect((self.width - size) // 2, self.height - size - margin, size, size),
            "LEFT":  QRect(margin, (self.height - size) // 2, size, size),
            "RIGHT": QRect(self.width - size - margin, (self.height - size) // 2, size, size),
            "CLICK": QRect((self.width - size) // 2, (self.height - size) // 2, size, size)
        }
        
        return [Stimulus(name, rect, freq_by_cmd.get(name, 0)) for name, rect in pos.items()]

    def update_screen(self):
        self.frame_counter += 1
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        
        for stim in self.stimuli:
            if stim.freq > 0:
                # --- KLUCZOWA POPRAWKA MATEMATYCZNA ---
                # Używamy funkcji sinus lub prostokąta opartej na czasie/klatkach
                # L = 0.5 * (1 + sign(sin(2 * pi * f * t)))
                
                phase = 2 * np.pi * stim.freq * (self.frame_counter / self.refresh_rate)
                if np.sin(phase) > 0:
                    qp.fillRect(stim.rect, stim.color)

def run_overlay(cmd_queue):
    app = QApplication(sys.argv)
    window = OverlayWindow(cmd_queue)
    sys.exit(app.exec_())