# config.py

# Konfiguracja OpenBCI Cyton
BOARD_ID = -1  # BrainFlow BoardIds.CYTON_BOARD
SERIAL_PORT = 'COM5' 
EEG_CHANNELS = [1, 2, 3, 4, 5, 6, 7, 8] # Wszystkie kanały
ACTIVE_CHANNELS = [6, 7, 8] # interesują nas O1, O2, Oz (wg  są to zwykle kanały 5-8 na Cytonie zależy od montażu)

# Częstotliwości stymulacji (Targety)
STIMULI_MAP = {
    2.0: "UP",
    3.0: "DOWN",
    12: "LEFT",
    8: "RIGHT",
    10: "CLICK"
}

SAMPLING_RATE = 250   # Hz dla Cytona
WINDOW_DURATION = 4.0 # Sekundy (okno czasowe)