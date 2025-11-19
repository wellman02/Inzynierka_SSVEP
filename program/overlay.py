import sys
import keyboard
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import subprocess

class OverlayWindow(QMainWindow):
    def __init__(self, stimuli):
        super().__init__()
        self.stimuli = stimuli

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.NoDropShadowWindowHint |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

    def paintEvent(self, event):
        qp = QPainter(self)
        for stim in self.stimuli:
            qp.fillRect(stim.rect, stim.get_qcolor())
        
    def close(self):
        super().close()

class Stimulus:
    def __init__(self, rect: QRect, color, blink_frequency=0, opacity=50):
        self.rect = rect
        self.color = QColor(color)
        self.blink_frequency = blink_frequency
        self.opacity = int(opacity)  # 0-100%
        self.color.setAlpha(int(self.opacity * 255 / 100))


    def get_qcolor(self):
        c = QColor(self.color)
        c.setAlpha(int(self.opacity * 255 / 100))
        return c

class Controller:
    def __init__(self):
        self.app = QApplication(sys.argv)

        screen = QApplication.primaryScreen().size()
        screen_w, screen_h = screen.width(), screen.height()
        self.refresh_rate = int(subprocess.check_output('wmic PATH Win32_videocontroller get currentrefreshrate').split(b'\n')[1].strip().decode())

        center_x = screen_w // 2
        center_y = screen_h // 2
        
        # domyslne parametry stymulacji
        self.visible = True
        stimuli_width = 200
        stimuli_height = 200
        color = QColor(0, 255, 0, 128)


        self.stimuli = [
            Stimulus(QRect(0, center_y - stimuli_height//2, stimuli_width, stimuli_height), color),                       # lewy
            Stimulus(QRect(screen_w - stimuli_width, center_y - stimuli_height//2, stimuli_width, stimuli_height), color),       # prawy
            Stimulus(QRect(center_x - stimuli_width//2, 0, stimuli_width, stimuli_height), color),                       # gora
            Stimulus(QRect(center_x - stimuli_width//2, screen_h - stimuli_height, stimuli_width, stimuli_height), color),       # dol
            Stimulus(QRect(center_x - stimuli_width//2, center_y - stimuli_height//2, stimuli_width, stimuli_height), color)          # srodek
        ]

        self.overlay = OverlayWindow(self.stimuli)
        self.overlay.show()

        self.settings_window = SettingsWindow(self.stimuli, self.overlay)

        # skróty globalne
        keyboard.add_hotkey("ctrl+shift+z", self.toggle_overlay)
        keyboard.add_hotkey("ctrl+shift+x", self.app.quit)
        
        # skróty lokalne
        settings_shortcut = QShortcut("Ctrl+Shift+O", self.overlay)
        settings_shortcut.activated.connect(self.open_settings)
    
    def open_settings(self):
        if not self.settings_window.isVisible():
            self.settings_window.show()
    
    def toggle_overlay(self):
        if self.visible:
            self.overlay.hide()
            self.visible = False
        else:
            self.overlay.showFullScreen()
            self.visible = True
    
    def run(self):
        sys.exit(self.app.exec_())

class SettingsWindow(QWidget):
    def __init__(self, stimuli, overlay):
        super().__init__()
        self.stimuli = stimuli
        self.overlay = overlay

        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 350)

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # lista stymulacji
        self.list_widget = QListWidget()
        for i in range(len(self.stimuli)):
            item = QListWidgetItem(f"Stimulus {i+1}")
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        
        # panel edycji
        edit_layout = QVBoxLayout()
        
        # Kolor
        self.color_button = QPushButton("Change Color")
        self.color_button.clicked.connect(self.change_color)
        edit_layout.addWidget(self.color_button)
        
        # Opacity (0-100%)
        self.opacity = QSpinBox(); self.opacity.setRange(0, 100)
        self.opacity.valueChanged.connect(self.change_opacity)
        edit_layout.addWidget(QLabel("Opacity (%):")); edit_layout.addWidget(self.opacity)
        
        # X, Y, Width, Height
        self.x_spin = QSpinBox(); self.x_spin.setRange(0, 5000)
        self.y_spin = QSpinBox(); self.y_spin.setRange(0, 5000)
        self.w_spin = QSpinBox(); self.w_spin.setRange(1, 5000)
        self.h_spin = QSpinBox(); self.h_spin.setRange(1, 5000)

        for s in [self.x_spin, self.y_spin, self.w_spin, self.h_spin]:
            s.valueChanged.connect(self.update_geometry)
        
        edit_layout.addWidget(QLabel("X")); edit_layout.addWidget(self.x_spin)
        edit_layout.addWidget(QLabel("Y")); edit_layout.addWidget(self.y_spin)
        edit_layout.addWidget(QLabel("Width")); edit_layout.addWidget(self.w_spin)
        edit_layout.addWidget(QLabel("Height")); edit_layout.addWidget(self.h_spin)
        
        layout.addLayout(edit_layout)
        
        self.list_widget.currentRowChanged.connect(self.load_stimulus)
        self.list_widget.setCurrentRow(0)
        
    def load_stimulus(self, index):
        self.loading = True
        stim = self.stimuli[index]
        rect = stim.rect
        
        self.x_spin.setValue(rect.x())
        self.y_spin.setValue(rect.y())
        self.w_spin.setValue(rect.width())
        self.h_spin.setValue(rect.height())
        
        self.opacity.setValue(int(stim.opacity))
        
        self.loading = False
        
    def change_color(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        stim = self.stimuli[idx]
        color = QColorDialog.getColor(stim.color)
        if color.isValid():
            # keep opacity from stim.opacity
            color.setAlpha(int(stim.opacity * 255 / 100))
            stim.color = color
            self.overlay.update()


    def change_opacity(self, value):
        # value comes from QSpinBox; ignore if loading
        if self.loading:
            return
        idx = self.list_widget.currentRow()
        if idx < 0:
            return

        try:
            pct = int(value)
        except (TypeError, ValueError):
            pct = int(self.opacity.value())
        pct = max(0, min(100, pct))

        stim = self.stimuli[idx]
        stim.opacity = pct
        # keep QColor alpha in sync
        stim.color.setAlpha(int(pct * 255 / 100))
        self.overlay.update()


    def update_geometry(self, *args):
        if self.loading:
            return
        idx = self.list_widget.currentRow()
        if idx < 0:
            return
        stim = self.stimuli[idx]

        x = self.x_spin.value()
        y = self.y_spin.value()
        w = self.w_spin.value()
        h = self.h_spin.value()
        stim.rect = QRect(x, y, w, h)
        self.overlay.update()
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()
        
def create_overlay():
    controller = Controller()
    controller.run()
