# Konfiguracja OpenBCI Cyton
BOARD_ID = 0  # BrainFlow BoardIds.CYTON_BOARD
SERIAL_PORT = 'COM5' 
EEG_CHANNELS = [1, 2, 3, 4, 5, 6, 7, 8] # Wszystkie kanały
ACTIVE_CHANNELS = [6, 7, 8] # interesują nas O1, O2, Oz

# Częstotliwości stymulacji
STIMULI_MAP = {
    6.66: "UP",
    7.5: "DOWN",
    8.57: "LEFT",
    10.0: "RIGHT",
    12.0: "CLICK"
}

SAMPLING_RATE = 250
WINDOW_DURATION = 4.0 
THRESHOLD_CCA = 0.3