import sys
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ttest_rel
import mne

def snr_spectrum(psd, noise_n_neighbor_freqs=1, noise_skip_neighbor_freqs=1):
    """Compute SNR spectrum from PSD spectrum using convolution.

    Parameters
    ----------
    psd : ndarray, shape ([n_trials, n_channels,] n_frequency_bins)
        Data object containing PSD values. Works with arrays as produced by
        MNE's PSD functions or channel/trial subsets.
    noise_n_neighbor_freqs : int
        Number of neighboring frequencies used to compute noise level.
        increment by one to add one frequency bin ON BOTH SIDES
    noise_skip_neighbor_freqs : int
        set this >=1 if you want to exclude the immediately neighboring
        frequency bins in noise level calculation

    Returns
    -------
    snr : ndarray, shape ([n_trials, n_channels,] n_frequency_bins)
        Array containing SNR for all epochs, channels, frequency bins.
        NaN for frequencies on the edges, that do not have enough neighbors on
        one side to calculate SNR.
    """
    # Construct a kernel that calculates the mean of the neighboring
    # frequencies
    averaging_kernel = np.concatenate(
        (
            np.ones(noise_n_neighbor_freqs),
            np.zeros(2 * noise_skip_neighbor_freqs + 1),
            np.ones(noise_n_neighbor_freqs),
        )
    )
    averaging_kernel /= averaging_kernel.sum()

    # Calculate the mean of the neighboring frequencies by convolving with the
    # averaging kernel.
    mean_noise = np.apply_along_axis(
        lambda psd_: np.convolve(psd_, averaging_kernel, mode="valid"), axis=-1, arr=psd
    )

    # The mean is not defined on the edges so we will pad it with nas. The
    # padding needs to be done for the last dimension only so we set it to
    # (0, 0) for the other ones.
    edge_width = noise_n_neighbor_freqs + noise_skip_neighbor_freqs
    pad_width = [(0, 0)] * (mean_noise.ndim - 1) + [(edge_width, edge_width)]
    mean_noise = np.pad(mean_noise, pad_width=pad_width, constant_values=np.nan)

    return psd / mean_noise


def analyze_data():
    """Analiza danych SSVEP"""
    # wczytanie danych
    data_path = mne.datasets.sample.data_path()
    bids_fname = (data_path / "sub-02" / "ses-01" / "eeg" / "sub-02_ses-01_task-ssvep_eeg.vhdr")
    raw = mne.io.read_raw_brainvision(bids_fname, preload=True, verbose=False)
    
    raw.info["line_freq"] = 50.0 # częstotliwosc sieci elektrycznej w polsce    
    
    # ustawienie standardu elektrod
    montage = mne.channels.make_standard_montage("standard_1020") 
    raw.set_montage(montage)

    # ustawienie sredniej referencji
    raw.set_eeg_reference("average", projection=True)

    # filtr dolno i górno przepustowy
    raw.filter(l_freq=1.0, h_freq=40.0, fir_design="firwin")

    # Construct epochs
    raw.annotations.rename({"Stimulus/S255": "12hz", "Stimulus/S155": "15hz"})
    tmin, tmax = -1.0, 20.0  # in s
    baseline = None
    epochs = mne.Epochs(
        raw,
        event_id=["12hz", "15hz"],
        tmin=tmin,
        tmax=tmax,
        baseline=baseline,
        verbose=False,
    )
    
    tmin = 1.0
    tmax = 20.0
    fmin = 1.0
    fmax = 90.0
    sfreq = epochs.info["sfreq"]

    spectrum = epochs.compute_psd(
        "welch",
        n_fft=int(sfreq * (tmax - tmin)),
        n_overlap=0,
        n_per_seg=None,
        tmin=tmin,
        tmax=tmax,
        fmin=fmin,
        fmax=fmax,
        window="boxcar",
        verbose=False,
    )
    psds, freqs = spectrum.get_data(return_freqs=True)
    
    snrs = snr_spectrum(psds, noise_n_neighbor_freqs=3, noise_skip_neighbor_freqs=1)

    fig, axes = plt.subplots(2, 1, sharex="all", sharey="none", figsize=(8, 5))
    freq_range = range(
    np.where(np.floor(freqs) == 1.0)[0][0], np.where(np.ceil(freqs) == fmax - 1)[0][0]
    )

    psds_plot = 10 * np.log10(psds)
    psds_mean = psds_plot.mean(axis=(0, 1))[freq_range]
    psds_std = psds_plot.std(axis=(0, 1))[freq_range]
    axes[0].plot(freqs[freq_range], psds_mean, color="b")
    axes[0].fill_between(
    freqs[freq_range], psds_mean - psds_std, psds_mean + psds_std, color="b", alpha=0.2
    )
    axes[0].set(title="PSD spectrum", ylabel="Power Spectral Density [dB]")

    # SNR spectrum
    snr_mean = snrs.mean(axis=(0, 1))[freq_range]
    snr_std = snrs.std(axis=(0, 1))[freq_range]

    axes[1].plot(freqs[freq_range], snr_mean, color="r")
    axes[1].fill_between(freqs[freq_range], snr_mean - snr_std, snr_mean + snr_std, color="r", alpha=0.2)
    axes[1].set(
    title="SNR spectrum",
    xlabel="Frequency [Hz]",
    ylabel="SNR",
    ylim=[-2, 30],
    xlim=[fmin, fmax],
    )
    fig.show()

