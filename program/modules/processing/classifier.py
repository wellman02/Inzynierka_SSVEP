import numpy as np
from .signal_utils import filter_signal, compute_fft, compute_psd

# Algorytm 3.3: Klasyfikator SNR 
def compute_snr(freqs, psd, fb, bw=1.0, n_harmonics=2):
    """
    SNR z uwzględnieniem harmonicznych 2*fb, 3*fb itd.
    Zwiększa czułość detekcji SSVEP.
    """
    sig_total = 0.0
    noise_total = 0.0
    
    for h in range(1, n_harmonics + 1):
        f = fb * h
        if f > freqs[-1]:   # harmoniczna poza zakresem
            break
            
        mask_sig = (freqs >= f - 0.5) & (freqs <= f + 0.5)
        mask_noise = (freqs >= f - bw) & (freqs <= f + bw) & (~mask_sig)
        
        if mask_sig.any() and mask_noise.any():
            sig_total += np.mean(psd[mask_sig])
            noise_total += np.mean(psd[mask_noise])
    
    if noise_total == 0:
        return 0.0
    return sig_total / noise_total

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