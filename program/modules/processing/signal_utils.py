import numpy as np
from functools import lru_cache
from mne.filter import filter_data
from scipy.signal import iirnotch, lfilter

def filter_signal(data: np.ndarray, fs: int) -> np.ndarray:
    """
    Filtracja zero-phase (bez przesunięcia fazowego):
    1. Bandpass 1–40 Hz (FIR, metoda 'fir')
    2. Notch 50 Hz
    data: (n_samples,)
    """
    # MNE oczekuje (n_channels, n_samples) — dodajemy wymiar
    x = data[np.newaxis, :]

    x = filter_data(
        x, sfreq=fs,
        l_freq=1.0, h_freq=40.0,
        method='fir',
        fir_window='hamming',
        verbose=False
    )
    
    b_n, a_n = _notch_coeffs(fs)
    x = lfilter(b_n, a_n, x)
    return x[0]  # z powrotem (n_samples,)


@lru_cache(maxsize=4)
def _notch_coeffs(fs):
    return iirnotch(50.0, 30.0, fs)

