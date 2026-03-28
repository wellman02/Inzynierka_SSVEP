import time
import queue
import traceback
import numpy as np
from collections import deque
from brainflow.board_shim import BoardShim, BrainFlowInputParams

from config import (SERIAL_PORT, BOARD_ID, SAMPLING_RATE,
                    WINDOW_DURATION, ACTIVE_CHANNELS, STIMULI_MAP)
from modules.processing.signal_utils import filter_signal, compute_fft, compute_psd
from modules.processing.classifier import compute_snr
from utils.mouse_controller import MouseController

# --- KONFIGURACJA FILTRÓW DECYZYJNYCH ---
THRESHOLD = 2.2        # Próg SNR 
REQUIRED_STABILITY = 3   # Liczba powtórzeń dla stabilizacji
# ----------------------------------------

COOLDOWN_SECONDS = 2.0

last_command_time = 0.0

def run_bci_loop(cmd_queue, fft_queue=None):
    params = BrainFlowInputParams()
    params.serial_port = SERIAL_PORT
    board = BoardShim(BOARD_ID, params)
    mouse = MouseController()
    
    try:
        board.prepare_session()
        board.start_stream()
        print("--- BCI START ---")

        n_samples = int(SAMPLING_RATE * WINDOW_DURATION)
        target_freqs = list(STIMULI_MAP.keys())
        buffer = deque(maxlen=REQUIRED_STABILITY)
        
        eeg_channels = BoardShim.get_eeg_channels(BOARD_ID)
        indices = [ch - 1 for ch in ACTIVE_CHANNELS]

        if max(indices) >= len(eeg_channels):
            raise ValueError(
                f"ACTIVE_CHANNELS {ACTIVE_CHANNELS} poza zakresem. "
                f"Dostępne kanały EEG: {len(eeg_channels)}"
            )
    
        consecutive = 0
        last_detected = None
    
        while True:
            time.sleep(0.1)
            data = board.get_current_board_data(n_samples)
            if data.shape[1] < n_samples: 
                continue

            # Pobranie kanałów EEG
            raw_eeg = data[eeg_channels]

            # Wybór kanałów potylicznych 
            occipital_data = raw_eeg[indices, :]

            # Filtracja
            filtered_channels = [filter_signal(ch, SAMPLING_RATE) for ch in occipital_data]
            
            
            # FFT i PSD
            all_psds = []
            all_ffts = []
            freqs = None
            
            for f_data in filtered_channels:
                f, psd = compute_psd(f_data, SAMPLING_RATE)
                _, fft_amp = compute_fft(f_data, SAMPLING_RATE)
                all_psds.append(psd)
                all_ffts.append(fft_amp)
                freqs = f

            avg_psd = np.mean(all_psds, axis=0)
            avg_fft = np.mean(all_ffts, axis=0)

            if fft_queue is not None:
                try:
                    fft_queue.put(
                        (freqs, avg_fft, filtered_channels, avg_psd),
                        block=False
                    )
                except queue.Full:
                    pass

            

            # Klasyfikacja SNR na PSD
            scores = {f: compute_snr(freqs, avg_psd, f) for f in target_freqs}
            detected_f = max(scores, key=scores.get)
            current_snr = scores[detected_f]

            # Logowanie dla celów diagnostycznych
            print(f"DEBUG: Max Freq: {detected_f}Hz | SNR: {current_snr:.2f} | Buffer: {list(buffer)}")

            if current_snr > THRESHOLD:
                if detected_f == last_detected:
                    consecutive += 1
                else:
                    consecutive = 1
                    last_detected = detected_f
            else:
                consecutive = 0
                last_detected = None

            if consecutive >= REQUIRED_STABILITY:
                command = STIMULI_MAP[last_detected]
                print(f">>> WYKRYTO: {command} (SNR: {current_snr:.2f})")
                mouse.execute(command)
                cmd_queue.put(command)
                consecutive = 0
                last_detected = None

    except Exception as e:
        print(f"Błąd krytyczny: {e}")
        traceback.print_exc()
    finally:
        if board.is_prepared():
            board.stop_stream()
            board.release_session()
