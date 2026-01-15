from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QSpinBox, QComboBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt

class SettingsWindow(QWidget):
    def __init__(self, stimuli):
        super().__init__()
        self.stimuli = stimuli
        self.setWindowTitle("Konfiguracja Stymulatora SSVEP")
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        
        # Lista obiektów stymulujących
        self.list_widget = QListWidget()
        for stim in self.stimuli:
            self.list_widget.addItem(stim.name)
        self.list_widget.currentRowChanged.connect(self.load_stimulus_settings)
        
        # Panel edycji
        self.edit_panel = QVBoxLayout()
        
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0, 60)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.valueChanged.connect(self.update_stimulus)

        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setSuffix(" %")
        self.opacity_spin.valueChanged.connect(self.update_stimulus)

        self.edit_panel.addWidget(QLabel("Częstotliwość:"))
        self.edit_panel.addWidget(self.freq_spin)
        self.edit_panel.addWidget(QLabel("Przezroczystość:"))
        self.edit_panel.addWidget(self.opacity_spin)
        self.edit_panel.addStretch()

        layout.addWidget(self.list_widget)
        layout.addLayout(self.edit_panel)
        self.setLayout(layout)

    def load_stimulus_settings(self, index):
        if index < 0: return
        stim = self.stimuli[index]
        self.freq_spin.setValue(stim.blink_frequency)
        self.opacity_spin.setValue(stim.opacity)

    def update_stimulus(self):
        index = self.list_widget.currentRow()
        if index < 0: return
        
        stim = self.stimuli[index]
        stim.blink_frequency = self.freq_spin.value()
        stim.opacity = self.opacity_spin.value()