# Konfiguracja OpenBCI Cyton
BOARD_ID = -1  # BrainFlow BoardIds.CYTON_BOARD
SERIAL_PORT = 'COM5' 
EEG_CHANNELS = [1, 2, 3, 4, 5, 6, 7, 8] # Wszystkie kanały
ACTIVE_CHANNELS = [6, 7, 8] # interesują nas O1, O2, Oz (wg  są to zwykle kanały 5-8 na Cytonie zależy od montażu)

# Częstotliwości stymulacji
STIMULI_MAP = {
    2.0: "UP",
    3.0: "DOWN",
    5.0: "LEFT",
    7.5: "RIGHT",
    4.5: "CLICK"
}

SAMPLING_RATE = 250
WINDOW_DURATION = 4.0 # okno czasowe [s]