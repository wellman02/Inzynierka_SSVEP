import time
import numpy as np
from collections import deque
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations

from config import SERIAL_PORT, BOARD_ID, SAMPLING_RATE, WINDOW_DURATION, ACTIVE_CHANNELS, STIMULI_MAP
from modules.processing import compute_psd, classify_snr 
from modules.processing.signal_utils import filter_signal, compute_fft
from utils.mouse_controller import MouseController
from modules.processing.classifier import compute_snr

# --- KONFIGURACJA FILTRÓW DECYZYJNYCH ---
THRESHOLD = 2.2        # Próg SNR (dostosuj na podstawie DEBUG)
REQUIRED_STABILITY = 3   # Liczba powtórzeń dla stabilizacji
# ----------------------------------------

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
    
        while True:
            time.sleep(0.1)
            data = board.get_current_board_data(n_samples)
            if data.shape[1] < n_samples: 
                continue

            # 1. Pobranie kanałów EEG
            eeg_channels = BoardShim.get_eeg_channels(BOARD_ID)
            raw_eeg = data[eeg_channels]

            # 2. Wybór kanałów potylicznych zdefiniowanych w config.py
            indices = [ch - 1 for ch in ACTIVE_CHANNELS]
            occipital_data = raw_eeg[indices, :]
            
            # 3. Obliczanie FFT dla każdego kanału
            all_ffts = []
            freqs = None

            for ch_data in occipital_data:
                # Filtracja (Bandpass + Notch) zgodnie z signal_utils.py
                f_data = filter_signal(ch_data, SAMPLING_RATE)
                
                # Obliczenie FFT dla danego kanału
                current_freqs, current_fft = compute_fft(f_data, SAMPLING_RATE)
                
                all_ffts.append(current_fft)
                freqs = current_freqs

            # Sumowanie amplitud z kanałów (uśrednianie)
            avg_fft = np.mean(all_ffts, axis=0)

            # Wysłanie danych FFT + raw EEG do wizualizacji (jeśli kolejka istnieje)
            if fft_queue is not None:
                try:
                    # Wysyłamy: (freqs, psd, lista raw EEG dla każdego kanału)
                    fft_queue.put((freqs, avg_fft, [filter_signal(ch, SAMPLING_RATE) for ch in occipital_data]), block=False)
                except:
                    pass  # Kolejka pełna, pomiń tę ramkę

            # 4. Klasyfikacja SNR
            
            scores = {}
            for f in target_freqs:
                scores[f] = compute_snr(freqs, avg_fft, f)
            
            detected_f = max(scores, key=scores.get)
            current_snr = scores[detected_f]

            # Logowanie dla celów diagnostycznych
            print(f"DEBUG: Max Freq: {detected_f}Hz | SNR: {current_snr:.2f} | Buffer: {list(buffer)}")

            # 5. Logika decyzyjna
            if current_snr > THRESHOLD:
                buffer.append(detected_f)
            else:
                buffer.append(None)

            if len(buffer) == REQUIRED_STABILITY and all(x == buffer[0] and x is not None for x in buffer):
                command = STIMULI_MAP[buffer[0]]
                print(f" >>> WYKRYTO: {command} (SNR: {current_snr:.2f})")
                
                mouse.execute(command)
                cmd_queue.put(command)
                buffer.clear() 

    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        if board.is_prepared():
            board.stop_stream()
            board.release_session()