import numpy as np
from .signal_utils import compute_psd

# Algorytm 3.3: Klasyfikator SNR 
def compute_snr(freqs, psd, fb, bw=1.0):
    # Szukamy sygnału w paśmie +/- 0.5 Hz
    mask_sig = (freqs >= fb - 0.5) & (freqs <= fb + 0.5)
    
    # Szum to otoczenie +/- bw, z wyłączeniem sygnału
    mask_noise = (freqs >= fb - bw) & (freqs <= fb + bw) & (~mask_sig)
    
    sig = np.mean(psd[mask_sig])
    noise = np.mean(psd[mask_noise])
    
    if noise == 0: return 0
    return sig / noise

def classify_snr(x, fs, freqs_targets):
    """
    x: surowy sygnał z JEDNEGO kanału (np. O1 lub uśredniony)
    """
    freqs, psd = compute_psd(x, fs)
    # Oblicz SNR dla każdej częstotliwości docelowej
    scores = {f: compute_snr(freqs, psd, f) for f in freqs_targets}
    
    # Zwróć częstotliwość z najwyższym SNR
    best_freq = max(scores, key=scores.get)
    return best_freq, scores