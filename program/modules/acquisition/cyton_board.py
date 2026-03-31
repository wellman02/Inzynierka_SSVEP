import time
import traceback
from collections import deque
from brainflow.board_shim import BoardShim, BrainFlowInputParams

from config import (SERIAL_PORT, BOARD_ID, SAMPLING_RATE, WINDOW_DURATION, 
                    ACTIVE_CHANNELS, STIMULI_MAP, CLASSIFIER_METHOD, 
                    THRESHOLD_SNR, THRESHOLD_CCA)
from modules.processing.classifier import classify
from utils.mouse_controller import MouseController

REQUIRED_STABILITY = 3
COOLDOWN_SECONDS = 0.5

def run_bci_loop(cmd_queue):
    params = BrainFlowInputParams()
    params.serial_port = SERIAL_PORT
    board = BoardShim(BOARD_ID, params)
    mouse = MouseController()
    
    try:
        board.prepare_session()
        board.start_stream()
        print(f"--- BCI START (Metoda: {CLASSIFIER_METHOD}) ---")

        n_samples = int(SAMPLING_RATE * WINDOW_DURATION)
        target_freqs = list(STIMULI_MAP.keys())
        
        eeg_channels = BoardShim.get_eeg_channels(BOARD_ID)
        indices = [ch - 1 for ch in ACTIVE_CHANNELS]

        if max(indices) >= len(eeg_channels):
            raise ValueError(f"ACTIVE_CHANNELS {ACTIVE_CHANNELS} poza zakresem.")
    
        consecutive = 0
        last_detected = None
        active_threshold = THRESHOLD_CCA if CLASSIFIER_METHOD == "CCA" else THRESHOLD_SNR
    
        last_command_time = 0.0
    
        while True:
            time.sleep(0.1)
            data = board.get_current_board_data(n_samples)
            if data.shape[1] < n_samples: 
                continue

            # Pobranie danych potylicznych
            occipital_data = data[eeg_channels][indices, :]

            detected_f, current_score, scores, freqs, avg_fft, avg_psd, filtered_channels = classify(
                occipital_data, SAMPLING_RATE, target_freqs, method=CLASSIFIER_METHOD
            )

            # Logowanie
            # print(f"DEBUG: Max Freq: {detected_f}Hz | Wynik: {current_score:.2f} | Próg: {active_threshold}")

            # Logika stabilności i komend
            if current_score > active_threshold:
                if detected_f == last_detected:
                    consecutive += 1
                else:
                    consecutive = 1
                    last_detected = detected_f
            else:
                consecutive = 0
                last_detected = None

            if consecutive >= REQUIRED_STABILITY:
                if time.time() - last_command_time >= COOLDOWN_SECONDS:
                    command = STIMULI_MAP[last_detected]
                    print(f">>> WYKRYTO: {command} (Wynik: {current_score:.2f})")
                    mouse.execute(command)
                    cmd_queue.put(command)
                    last_command_time = time.time()
                
                consecutive = 0
                last_detected = None

    except Exception as e:
        print(f"Błąd krytyczny: {e}")
        traceback.print_exc()
    finally:
        if board.is_prepared():
            board.stop_stream()
            board.release_session()