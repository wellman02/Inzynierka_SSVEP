import sys
from multiprocessing import Process, Queue

from modules.stimulation import run_overlay
from modules.acquisition.cyton_board import run_bci_loop

def main():
    cmd_queue = Queue()

    # Moduł stymulujący (GUI)
    stimulation_process = Process(
        target=run_overlay, 
        args=(cmd_queue,), 
        name="Stimulation_Module"
    )

    # Moduł rejestracji i przetwarzania 
    acquisition_process = Process(
        target=run_bci_loop, 
        args=(cmd_queue,), 
        name="Acquisition_Processing_Module"
    )
    print("--- Uruchamianie Systemu SSVEP ---")
    
    try:
        # 3. Start procesów
        stimulation_process.start()
        acquisition_process.start()

        # Czekaj na zamknięcie okna GUI (główny wątek tu zostanie)
        stimulation_process.join()
    except KeyboardInterrupt:
        print("\nPrzerwano ręcznie...")
    finally:
        for proc in [acquisition_process, stimulation_process]:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=3)
        print("System wyłączony.")

if __name__ == "__main__":
    main()


