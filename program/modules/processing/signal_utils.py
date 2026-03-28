import numpy as np
from functools import lru_cache
from scipy.signal import butter, lfilter, iirnotch


@lru_cache(maxsize=4)
def _butter_coeffs(fs):
    nyq = 0.5 * fs
    return butter(4, [1.0 / nyq, 40.0 / nyq], btype='band')

@lru_cache(maxsize=4)
def _notch_coeffs(fs):
    return iirnotch(50.0, 30.0, fs)

@lru_cache(maxsize=4)
def _hanning(N):
    return np.hanning(N)


def filter_signal(data, fs):
    b, a = _butter_coeffs(fs)
    y = lfilter(b, a, data)
    b_n, a_n = _notch_coeffs(fs)
    return lfilter(b_n, a_n, y)


def compute_fft(x, fs):
    N = len(x)
    w = _hanning(N)
    amp = np.abs(np.fft.rfft(x * w)) / (np.sum(w) / 2)
    freqs = np.fft.rfftfreq(N, 1.0 / fs)
    return freqs, amp


def compute_psd(x, fs):
    freqs, amp = compute_fft(x, fs)
    delta_f = freqs[1] - freqs[0]
    psd = (amp ** 2) / delta_f
    psd[1:-1] *= 2
    return freqs, psd