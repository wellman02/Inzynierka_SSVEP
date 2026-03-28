import numpy as np
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


def classify(occipital_data, fs, target_freqs):
    """
    Pełny pipeline: filtracja -> PSD -> SNR -> wykryta częstotliwość.

    Parametry:
        occipital_data : (n_channels, n_samples) surowe dane EEG
        fs             : częstotliwość próbkowania
        target_freqs   : lista częstotliwości bodźców

    Zwraca:
        detected_f, current_snr, scores, freqs, avg_fft, avg_psd, filtered_chs
    """
    all_psds, all_ffts, filtered_chs = [], [], []
    freqs = None

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

    scores     = {f: compute_snr(freqs, avg_psd, f) for f in target_freqs}
    detected_f = max(scores, key=scores.get)

    return detected_f, scores[detected_f], scores, freqs, avg_fft, avg_psd, filtered_chs