import sys
from multiprocessing import Process, Queue

from modules.stimulation import run_overlay
from modules.acquisition import run_bci_loop
from modules.visualization.fft_graph import run_fft_window

def main():
    # 1. Kolejka komunikacyjna (BCI -> System)
    cmd_queue = Queue()

    # 2. Definicja procesów
    # Proces A: Moduł stymulujący (GUI)
    stimulation_process = Process(
        target=run_overlay, 
        args=(cmd_queue,), 
        name="Stimulation_Module"
    )

    # Proces B: Moduł rejestracji i przetwarzania 
    acquisition_process = Process(
        target=run_bci_loop, 
        args=(cmd_queue,), 
        name="Acquisition_Processing_Module"
    )
    
    graph_process = Process(
        target=run_fft_window, 
        args=(cmd_queue,), 
        name="FFT_Window_Module"
    )

    print("--- Uruchamianie Systemu SSVEP ---")
    
    try:
        # 3. Start procesów
        stimulation_process.start()
        acquisition_process.start()
        graph_process.start()

        # Czekaj na zamknięcie okna GUI (główny wątek tu zostanie)
        stimulation_process.join()

    except KeyboardInterrupt:
        print("\nPrzerwano ręcznie...")
    finally:
        # 4. Sprzątanie
        if acquisition_process.is_alive():
            acquisition_process.terminate()
        if stimulation_process.is_alive():
            stimulation_process.terminate()
        print("System wyłączony.")

if __name__ == "__main__":
    main()