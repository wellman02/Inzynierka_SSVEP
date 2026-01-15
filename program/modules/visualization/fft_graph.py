import sys
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from config import SAMPLING_RATE, STIMULI_MAP, ACTIVE_CHANNELS


import sys
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from config import SAMPLING_RATE, STIMULI_MAP, ACTIVE_CHANNELS

class FFTWindow(QMainWindow):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.setWindowTitle("Real-time EEG Monitor - Raw Data + FFT + PSD")
        self.setGeometry(100, 100, 1400, 950)

        self.figure = Figure(figsize=(14, 10), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.freqs = None
        self.fft = np.zeros(1000)
        self.psd = np.zeros(1000) # Nowy bufor na dane PSD
        self.raw_eeg_channels = []
        self.time_axis = None
        
        self.target_freqs = list(STIMULI_MAP.keys())
        self.n_channels = len(ACTIVE_CHANNELS)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)

    def update_plot(self):
        try:
            while True:
                data = self.data_queue.get_nowait()
                # Oczekujemy teraz 4 elementów w krotce: freqs, fft, raw_eeg, psd
                self.freqs, self.fft, self.raw_eeg_channels, self.psd = data
                n_samples = self.raw_eeg_channels[0].shape[0] if len(self.raw_eeg_channels) > 0 else 1000
                self.time_axis = np.arange(n_samples) / SAMPLING_RATE
        except:
            pass

        if self.freqs is None or self.fft is None or self.psd is None:
            return

        self.figure.clear()

        # Zwiększamy liczbę wierszy o 2 (jeden dla FFT, jeden dla PSD)
        n_rows = self.n_channels + 2 
        
        # 1. Wykresy czasowe (Raw EEG)
        for ch_idx in range(self.n_channels):
            ax = self.figure.add_subplot(n_rows, 1, ch_idx + 1)
            if ch_idx < len(self.raw_eeg_channels) and self.time_axis is not None:
                ax.plot(self.time_axis, self.raw_eeg_channels[ch_idx], linewidth=1, color='darkblue')
            
            ax.set_ylabel(f'Ch {ACTIVE_CHANNELS[ch_idx]} (μV)', fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, self.time_axis[-1] if self.time_axis is not None else 4)
            ax.set_ylim(-50, 50)
            
        # 2. Wykres FFT (Amplituda)
        ax_fft = self.figure.add_subplot(n_rows, 1, n_rows - 1)
        ax_fft.plot(self.freqs, self.fft, linewidth=1.5, color='blue', label='FFT Amplitude')
        for freq in self.target_freqs:
            ax_fft.axvline(x=freq, color='red', linestyle='--', alpha=0.4, linewidth=1)
        
        ax_fft.set_xlim(1, 40)
        ax_fft.set_ylim(0, 10) # Stała skala zgodnie z Twoją zmianą
        ax_fft.set_ylabel('Amplituda', fontsize=9)
        ax_fft.set_title('Widmo Amplitudy (FFT)', fontsize=10, fontweight='bold')
        ax_fft.grid(True, alpha=0.3)
        ax_fft.legend(loc='upper right', fontsize=8)

        # 3. Wykres PSD (Moc)
        ax_psd = self.figure.add_subplot(n_rows, 1, n_rows)
        ax_psd.plot(self.freqs, self.psd, linewidth=1.5, color='green', label='PSD (μV²/Hz)')
        for freq in self.target_freqs:
            ax_psd.axvline(x=freq, color='red', linestyle='--', alpha=0.4, linewidth=1)
        
        ax_psd.set_xlim(1, 40)
        # Skala PSD jest zazwyczaj znacznie większa niż FFT (kwadrat wartości)
        ax_psd.set_ylim(0, 120)
        ax_psd.set_xlabel('Częstotliwość (Hz)', fontsize=9)
        ax_psd.set_ylabel('Moc (μV²/Hz)', fontsize=9)
        ax_psd.set_title('Gęstość Widmowa Mocy (PSD)', fontsize=10, fontweight='bold')
        ax_psd.grid(True, alpha=0.3)
        ax_psd.legend(loc='upper right', fontsize=8)

        self.figure.suptitle(f'Real-time EEG Monitor ({SAMPLING_RATE} Hz)', fontsize=12, fontweight='bold')
        self.figure.tight_layout(rect=[0, 0.03, 1, 0.95])
        self.canvas.draw()


def run_fft_window(data_queue):
    """Uruchomienie okna FFT w osobnym procesie"""
    app = QApplication(sys.argv)
    window = FFTWindow(data_queue)
    window.show()
    sys.exit(app.exec_())
