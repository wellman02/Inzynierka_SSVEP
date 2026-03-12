import numpy as np
from functools import lru_cache
from scipy.signal import butter, lfilter, iirnotch

# ---------------------------------------------------------------------------
# Buforowanie współczynników filtrów — obliczane raz dla danych parametrów
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    return butter(order, [lowcut / nyq, highcut / nyq], btype='band')

@lru_cache(maxsize=8)
def _notch_coeffs(notch_freq, quality_factor, fs):
    return iirnotch(notch_freq, quality_factor, fs)


def filter_signal(data, fs, lowcut=1.0, highcut=40.0, order=4):
    """
    Filtracja sygnału EEG:
    1. Filtr pasmowo-przepustowy Butterwortha 1–40 Hz
    2. Filtr zaporowy (notch) 50 Hz
    
    Współczynniki filtrów są buforowane — obliczane tylko raz.
    """
    b, a = _butter_bandpass(lowcut, highcut, fs, order)
    y = lfilter(b, a, data)

    b_notch, a_notch = _notch_coeffs(50.0, 30.0, fs)
    y = lfilter(b_notch, a_notch, y)

    return y

def _hanning_window(N):
    """
    Zwraca okno Hanninga długości N.
    Buforowane przez lru_cache — dla stałego N obliczane raz.
    """
    return np.hanning(N)

def compute_fft(x, fs):
    """
    Algorytm 3.1: Obliczanie FFT z oknem Hanninga.
    
    Okno redukuje przeciek widmowy — kluczowe dla dokładnej
    identyfikacji częstotliwości SSVEP.
    
    Zwraca:
        freqs   : tablica częstotliwości [Hz]
        amp     : amplituda widma (unormowana przez sumę okna)
    """
    N = len(x)
    window = _hanning_window(N)
    
    # Normalizacja przez sumę okna zachowuje poprawną amplitudę
    X = np.fft.rfft(x * window)
    amp = np.abs(X) / (np.sum(window) / 2)
    
    freqs = np.fft.rfftfreq(N, 1.0 / fs)
    return freqs, amp

def compute_psd(x, fs):
    """
    Algorytm 3.2: Jednostronna gęstość widmowa mocy (PSD).
    
    Korzysta z compute_fft (okno Hanninga + normalizacja).
    Mnoży przez 2 składowe poza DC i Nyquistem, żeby zachować
    całkowitą moc sygnału (jednostronne PSD).
    
    Jednostka: V²/Hz (lub µV²/Hz zależnie od jednostek wejścia)
    """
    freqs, amp = compute_fft(x, fs)
    
    # Moc = amplituda² / szerokość_prążka
    delta_f = freqs[1] - freqs[0]  # rozdzielczość częstotliwościowa
    psd = (amp ** 2) / delta_f
    
    # Mnożnik ×2 dla składowych jednostronnych (poza DC i Nyquistem)
    # DC (index 0) i Nyquist (ostatni) nie są mnożone
    psd[1:-1] *= 2
    
    return freqs, psd