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


# import time
# import queue
# import traceback
# import numpy as np
# from pathlib import Path
# from collections import deque
# from brainflow.board_shim import BoardShim, BrainFlowInputParams

# from config import SERIAL_PORT, BOARD_ID, SAMPLING_RATE, WINDOW_DURATION, ACTIVE_CHANNELS, STIMULI_MAP
# from modules.processing.classifier import classify
# from utils.mouse_controller import MouseController

# THRESHOLD          = 2.5
# REQUIRED_STABILITY = 3
# COOLDOWN_SECONDS   = 2.0
# MAX_AMPLITUDE_UV   = 100.0
# WARMUP_SECONDS     = 2.0


# # ---------------------------------------------------------------------------
# # Wczytywanie pliku RAW OpenBCI
# # ---------------------------------------------------------------------------

# def _load_raw_file(filepath):
#     """
#     Wczytuje plik RAW z OpenBCI GUI.
#     Zwraca tablicę (8, n_samples) w µV.
#     """
#     filepath = Path(filepath)
#     if not filepath.exists():
#         raise FileNotFoundError(f"Plik nie istnieje: {filepath}")

#     raw = np.genfromtxt(
#         filepath,
#         delimiter=',',
#         comments='%',
#         skip_header=1,
#         usecols=range(1, 9)   # kolumny 1–8 = kanały EEG
#     )

#     eeg = raw.T  # (8, n_samples)

#     # Zeruj próbki z saturacją (-187500 = brak sygnału)
#     eeg[np.abs(eeg + 187500.0) < 1.0] = 0.0

#     print(f"[RAW] Wczytano: {filepath.name} | "
#           f"Próbki: {eeg.shape[1]} | Czas: {eeg.shape[1]/SAMPLING_RATE:.1f}s")
#     return eeg


# # ---------------------------------------------------------------------------
# # Wspólna pętla klasyfikacji — używana przez oba tryby
# # ---------------------------------------------------------------------------

# def _classification_loop(get_data_fn, total_samples, cmd_queue, fft_queue, execute_commands):
#     """
#     Pętla klasyfikacji SSVEP.

#     Parametry:
#         get_data_fn      : funkcja() -> ndarray (8, n_samples) lub (8, 0) gdy koniec
#         total_samples    : całkowita liczba próbek (do logowania postępu)
#         cmd_queue        : kolejka komend
#         fft_queue        : kolejka wizualizacji
#         execute_commands : czy wykonywać komendy myszy
#     """
#     n_samples    = int(SAMPLING_RATE * WINDOW_DURATION)
#     target_freqs = list(STIMULI_MAP.keys())
#     indices      = [ch - 1 for ch in ACTIVE_CHANNELS]

#     consecutive       = 0
#     last_freq         = None
#     last_command_time = 0.0

#     while True:
#         data = get_data_fn()

#         # Koniec danych (tryb plik)
#         if data.shape[1] == 0:
#             print("[INFO] Koniec danych.")
#             break

#         if data.shape[1] < n_samples:
#             continue

#         occipital = data[indices, :]

#         # Odrzucanie artefaktów
#         if np.max(np.abs(occipital)) > MAX_AMPLITUDE_UV:
#             consecutive = 0
#             last_freq   = None
#             continue

#         # Klasyfikacja
#         detected_f, current_snr, scores, freqs, avg_fft, avg_psd, filtered_chs = classify(
#             occipital, SAMPLING_RATE, target_freqs
#         )

#         # Wizualizacja
#         if fft_queue is not None:
#             try:
#                 fft_queue.put((freqs, avg_fft, filtered_chs, avg_psd), block=False)
#             except queue.Full:
#                 pass

#         # Logowanie
#         progress = f"{100 * (data.shape[1] / total_samples):.0f}%" if total_samples else ""
#         print(f"[{progress}] {detected_f:.1f}Hz | SNR: {current_snr:.2f} | "
#               f"Consec: {consecutive}/{REQUIRED_STABILITY}")

#         # Licznik kolejnych trafień
#         if current_snr > THRESHOLD and detected_f == last_freq:
#             consecutive += 1
#         elif current_snr > THRESHOLD:
#             consecutive = 1
#             last_freq   = detected_f
#         else:
#             consecutive = 0
#             last_freq   = None

#         # Detekcja z cooldownem
#         now = time.time()
#         if consecutive >= REQUIRED_STABILITY and (now - last_command_time) >= COOLDOWN_SECONDS:
#             command = STIMULI_MAP[last_freq]
#             print(f">>> WYKRYTO: {command} (SNR: {current_snr:.2f})")
#             if execute_commands:
#                 MouseController().execute(command)
#             cmd_queue.put(command)
#             last_command_time = now
#             consecutive       = 0
#             last_freq         = None


# # ---------------------------------------------------------------------------
# # Tryb 1: Fizyczna płytka Cyton
# # ---------------------------------------------------------------------------

# def run_bci_loop(cmd_queue, fft_queue=None):
#     params = BrainFlowInputParams()
#     params.serial_port = SERIAL_PORT
#     board = BoardShim(BOARD_ID, params)

#     try:
#         board.prepare_session()
#         board.start_stream()

#         # Rozgrzewka — daj sygnałowi się ustabilizować
#         print(f"[INFO] Stabilizacja sygnału ({WARMUP_SECONDS}s)...")
#         time.sleep(WARMUP_SECONDS)
#         print("--- BCI START ---")

#         eeg_channels  = BoardShim.get_eeg_channels(BOARD_ID)
#         n_samples     = int(SAMPLING_RATE * WINDOW_DURATION)

#         def get_data():
#             time.sleep(0.1)
#             data = board.get_current_board_data(n_samples)
#             return data[eeg_channels]

#         _classification_loop(get_data, None, cmd_queue, fft_queue, execute_commands=True)

#     except Exception as e:
#         print(f"Błąd: {e}")
#         traceback.print_exc()
#     finally:
#         if board.is_prepared():
#             board.stop_stream()
#             board.release_session()
#         print("--- BCI STOP ---")


# # ---------------------------------------------------------------------------
# # Tryb 2: Plik RAW OpenBCI
# # ---------------------------------------------------------------------------

# def run_bci_loop_from_file(filepath, cmd_queue, fft_queue=None, execute_commands=False):
#     """
#     Parametry:
#         filepath         : ścieżka do pliku RAW OpenBCI
#         execute_commands : czy wykonywać ruchy myszy (domyślnie False dla trybu pliku)
#     """
#     try:
#         eeg_data      = _load_raw_file(filepath)
#         n_samples     = int(SAMPLING_RATE * WINDOW_DURATION)
#         total_samples = eeg_data.shape[1]
#         pos           = [0]  # lista żeby móc modyfikować w closure

#         def get_data():
#             time.sleep(0.05)
#             start = pos[0]
#             end   = start + n_samples
#             if end > total_samples:
#                 return np.zeros((8, 0))
#             pos[0] += n_samples // 2   # przesuń o połowę okna (50% overlap)
#             return eeg_data[:, start:end]

#         print("--- BCI START (plik RAW) ---")
#         _classification_loop(get_data, total_samples, cmd_queue, fft_queue, execute_commands)

#     except Exception as e:
#         print(f"Błąd (tryb plik): {e}")
#         traceback.print_exc()
#     finally:
#         print("--- BCI STOP ---")