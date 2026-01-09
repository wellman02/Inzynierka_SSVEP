import sys
from multiprocessing import Process, Queue


from modules.stimulation import run_overlay
from modules.acquisition import run_bci_loop
from modules.visualization import run_fft_window

def main():
    # 1. Kolejka komunikacyjna (BCI -> System)
    # Służy do przesyłania wykrytych komend z procesu analizy do sterownika
    cmd_queue = Queue()
    
    # 2. Kolejka do transmisji danych FFT (BCI -> Wizualizacja)
    fft_queue = Queue(maxsize=10)

    # 3. Definicja procesów
    # Proces A: Moduł stymulujący (GUI)
    stimulation_process = Process(
        target=run_overlay, 
        args=(cmd_queue,), 
        name="Stimulation_Module"
    )

    # Proces B: Moduł rejestracji i przetwarzania (Cyton + FFT/SNR)
    acquisition_process = Process(
        target=run_bci_loop, 
        args=(cmd_queue, fft_queue), 
        name="Acquisition_Processing_Module"
    )
    
    # Proces C: Wizualizacja FFT
    fft_process = Process(
        target=run_fft_window,
        args=(fft_queue,),
        name="FFT_Visualization_Module"
    )

    print("--- Uruchamianie Systemu SSVEP ---")
    
    try:
        # 4. Start procesów
        stimulation_process.start()
        acquisition_process.start()
        fft_process.start()

        # Czekaj na zamknięcie okna GUI (główny wątek tu zostanie)
        stimulation_process.join()

    except KeyboardInterrupt:
        print("\nPrzerwano ręcznie...")
    finally:
        # 5. Sprzątanie
        if acquisition_process.is_alive():
            acquisition_process.terminate()
        if stimulation_process.is_alive():
            stimulation_process.terminate()
        if fft_process.is_alive():
            fft_process.terminate()
        print("System wyłączony.")

if __name__ == "__main__":
    main()