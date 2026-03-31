import numpy as np
from sklearn.cross_decomposition import CCA
from .signal_utils import filter_signal, compute_fft, compute_psd

def compute_snr(freqs, psd, fb, bw=1.0, n_harmonics=2):
    """SNR z harmonicznymi dla częstotliwości bodźca fb."""
    sig, noise = 0.0, 0.0
    for h in range(1, n_harmonics + 1):
        f = fb * h
        if f > freqs[-1]:
            break
        mask_sig   = (freqs >= f - 0.5) & (freqs <= f + 0.5)
        mask_noise = (freqs >= f - bw)  & (freqs <= f + bw) & ~mask_sig
        if mask_sig.any() and mask_noise.any():
            sig   += np.mean(psd[mask_sig])
            noise += np.mean(psd[mask_noise])
    return sig / noise if noise > 0 else 0.0

def generate_references(freq, fs, n_samples, n_harmonics=2):
    """Generuje sygnały referencyjne (sin i cos) dla CCA."""
    t = np.arange(n_samples) / fs
    Y = []
    for h in range(1, n_harmonics + 1):
        Y.append(np.sin(2 * np.pi * freq * h * t))
        Y.append(np.cos(2 * np.pi * freq * h * t))
    return np.array(Y).T

def compute_cca(eeg_data, fs, target_freqs, n_harmonics=2):
    """Oblicza korelację kanoniczną dla każdej częstotliwości."""
    n_samples = eeg_data.shape[1]
    X = eeg_data.T 
    
    scores = {}
    cca = CCA(n_components=1)
    
    for freq in target_freqs:
        Y = generate_references(freq, fs, n_samples, n_harmonics)
        cca.fit(X, Y)
        X_c, Y_c = cca.transform(X, Y)
        corr = np.corrcoef(X_c[:, 0], Y_c[:, 0])[0, 1]
        scores[freq] = corr
        
    return scores

def classify(occipital_data, fs, target_freqs, method="SNR"):
    """
    Pełny pipeline: filtracja -> ekstrakcja cech (SNR lub CCA) -> wykryta częstotliwość.
    """
    all_psds, all_ffts, filtered_chs = [], [], []
    freqs = None

    # Zawsze filtrujemy i liczymy widmo (potrzebne do ewentualnego podglądu w GUI)
    for ch in occipital_data:
        f_data = filter_signal(ch, fs)
        filtered_chs.append(f_data)
        f, psd = compute_psd(f_data, fs)
        _, fft = compute_fft(f_data, fs)
        all_psds.append(psd)
        all_ffts.append(fft)
        freqs = f

    avg_psd = np.mean(all_psds, axis=0)
    avg_fft = np.mean(all_ffts, axis=0)

    # Wybór metody
    if method == "CCA":
        filtered_chs_np = np.array(filtered_chs)
        scores = compute_cca(filtered_chs_np, fs, target_freqs)
    else:
        scores = {f: compute_snr(freqs, avg_psd, f) for f in target_freqs}
        
    detected_f = max(scores, key=scores.get)
    current_score = scores[detected_f]

    return detected_f, current_score, scores, freqs, avg_fft, avg_psd, filtered_chs