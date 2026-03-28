import sys
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QSurfaceFormat, QCursor
from config import STIMULI_MAP

class Stimulus:
    def __init__(self, name, rect, freq, color=Qt.white, monitor_fps=60):
        self.name = name
        self.rect = rect
        self.freq = freq
        self.color = QColor(color)
        
        # Obliczamy liczbę klatek monitora na cykl
        if self.freq > 0:
            self.frames_per_cycle = monitor_fps / self.freq
        else:
            self.frames_per_cycle = 0

class OverlayWindow(QOpenGLWidget):
    def __init__(self, cmd_queue):
        super().__init__()
        self.frame_counter = 0
        
        # Wykrywamy rzeczywiste odświeżanie monitora (np. 180Hz)
        self.monitor_fps = self.get_refresh_rate()
        print(f"Monitor FPS: {self.monitor_fps} Hz")

        # Konfiguracja VSync
        fmt = QSurfaceFormat()
        fmt.setSwapInterval(1) 
        self.setFormat(fmt)

        screen_geom = QDesktopWidget().screenGeometry()
        self.width = screen_geom.width()
        self.height = screen_geom.height()
        
        self.stimuli = self.setup_dynamic_stimuli()

        # Ustawienia okna: Pełny ekran, zawsze na wierzchu
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # Ustawiamy czarne tło (nieprzezroczyste dla lepszego kontrastu)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)

        self.showFullScreen()
        
        # --- USTAWIENIE KURSORA NA ŚRODKU ---
        self.center_cursor()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0) 

    def get_refresh_rate(self):
        app = QApplication.instance()
        screen = app.primaryScreen()
        rate = screen.refreshRate()
        return rate if rate > 0 else 60.0

    def center_cursor(self):
        # Pobieramy geometrię ekranu i ustawiamy kursor na środku
        center = QPoint(self.width // 2, self.height // 2)
        QCursor.setPos(center)

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
        
        return [Stimulus(name, rect, freq_by_cmd.get(name, 0), monitor_fps=self.monitor_fps) 
                for name, rect in pos.items()]

    def paintEvent(self, event):
        self.frame_counter += 1
        
        qp = QPainter(self)
        # Malujemy tło na czarno w każdej klatce
        qp.fillRect(self.rect(), Qt.black)
        
        for stim in self.stimuli:
            if stim.freq > 0:
                # Logika podziału klatek (Square Wave)
                if (self.frame_counter % stim.frames_per_cycle) < (stim.frames_per_cycle / 2):
                    qp.fillRect(stim.rect, stim.color)

def run_overlay(cmd_queue):
    app = QApplication(sys.argv)
    window = OverlayWindow(cmd_queue)
    sys.exit(app.exec_())