import numpy as np
from sklearn.cross_decomposition import CCA
from .signal_utils import filter_signal

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

def classify(occipital_data, fs, target_freqs):
    """
    Pełny pipeline: filtracja -> ekstrakcja cech -> wykryta częstotliwość.
    """
    filtered_chs = []
    freqs = None

    # Zawsze filtrujemy i liczymy widmo (potrzebne do ewentualnego podglądu w GUI)
    for ch in occipital_data:
        f_data = filter_signal(ch, fs)
        filtered_chs.append(f_data)

    filtered_chs_np = np.array(filtered_chs)
    scores = compute_cca(filtered_chs_np, fs, target_freqs)
        
    detected_f = max(scores, key=scores.get)
    current_score = scores[detected_f]

    return detected_f, current_score, scores, freqs, filtered_chs