import numpy as np
from scipy.signal import butter, lfilter

def filter_signal(data, fs, lowcut=1.0, highcut=40.0, order=4):
    """
    Filtracja sygnału EEG zgodnie z założeniami pracy inżynierskiej.
    Wykorzystuje filtr Butterwortha.
    """
    # 1. Filtr pasmowo-przepustowy (Bandpass) 1-40 Hz
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, data)
    
    # 2. Filtr zaporowy (Notch) dla 50 Hz (zakłócenia sieci energetycznej)
    # Warto dodać, jeśli nie jest realizowany bezpośrednio w BrainFlow
    notch_freq = 50.0
    quality_factor = 30.0
    from scipy.signal import iirnotch
    b_notch, a_notch = iirnotch(notch_freq, quality_factor, fs)
    y = lfilter(b_notch, a_notch, y)
    
    return y

def compute_fft(x, fs):
    """Algorytm 3.1: Obliczanie FFT"""
    N = len(x)
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(N, 1/fs)
    return freqs, np.abs(X)

def compute_psd(x, fs):
    """Algorytm 3.2: Wyznaczanie gęstości widmowej mocy (PSD)"""
    N = len(x)
    X = np.fft.rfft(x)
    psd = (1.0 / (fs * N)) * (np.abs(X)**2) # Normalizacja PSD
    freqs = np.fft.rfftfreq(N, 1/fs)
    return freqs, psd