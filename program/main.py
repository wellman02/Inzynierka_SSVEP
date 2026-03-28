import sys
from multiprocessing import Process, Queue

from modules.stimulation import run_overlay
from modules.acquisition.cyton_board import run_bci_loop
from modules.visualization.fft_graph import run_fft_window

def main():
    # 1. Kolejka komunikacyjna (BCI -> System)
    cmd_queue = Queue()
    fft_queue = Queue(maxsize=5)

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
        args=(cmd_queue, fft_queue), 
        name="Acquisition_Processing_Module"
    )
    
    graph_process = Process(
        target=run_fft_window, 
        args=(fft_queue,), 
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
        for proc in [acquisition_process, stimulation_process, graph_process]:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=3)
        print("System wyłączony.")

if __name__ == "__main__":
    main()



# """
# Użycie:
#     python main.py                                    # fizyczna płytka
#     python main.py --file dane.txt                    # plik RAW OpenBCI
#     python main.py --file S001a.mat                   # wszystkie trialy MAMEM
#     python main.py --file S001a.mat --target 10.0     # tylko trialy 10.00 Hz
#     python main.py --file S001a.mat --target 8.57     # tylko trialy 8.57 Hz
#     python main.py --file S001a.mat --execute         # + ruchy myszy
# """

# import sys
# import time
# import argparse
# from multiprocessing import Process, Queue, freeze_support


# def parse_args():
#     p = argparse.ArgumentParser()
#     p.add_argument('--file',    type=str,   default=None,
#                    help='Plik RAW (.txt) lub MAMEM Dataset (.mat)')
#     p.add_argument('--target',  type=float, default=None,
#                    help='Częstotliwość bodźca Hz: 6.66 / 7.50 / 8.57 / 10.00 / 12.00')
#     p.add_argument('--execute', action='store_true',
#                    help='Wykonuj ruchy myszy w trybie offline')
#     return p.parse_args()


# def main():
#     args = parse_args()

#     cmd_queue = Queue()
#     fft_queue = Queue(maxsize=5)

#     from modules.stimulation import run_overlay
#     from modules.visualization.fft_graph import run_fft_window

#     if args.file is None:
#         from modules.acquisition.cyton_board import run_bci_loop
#         bci_fn   = run_bci_loop
#         bci_args = (cmd_queue, fft_queue)
#         print("Tryb: fizyczna płytka Cyton")

#     elif args.file.endswith('.mat'):
#         from modules.acquisition.mat_loader import run_bci_loop_from_mat
#         import functools
#         bci_fn = functools.partial(
#             run_bci_loop_from_mat,
#             args.file,
#             target_freq=args.target,
#             execute_commands=args.execute
#         )
#         bci_args = (cmd_queue, fft_queue)
#         freq_str = f"{args.target} Hz" if args.target else "wszystkie trialy"
#         print(f"Tryb: MAMEM .mat ({freq_str}) -> {args.file}")

#     else:
#         from modules.acquisition.cyton_board import run_bci_loop_from_file
#         import functools
#         bci_fn = functools.partial(
#             run_bci_loop_from_file,
#             args.file,
#             execute_commands=args.execute
#         )
#         bci_args = (cmd_queue, fft_queue)
#         print(f"Tryb: plik RAW -> {args.file}")

#     procs = [
#         Process(target=run_overlay,    args=(cmd_queue,),  name="Stimulation"),
#         Process(target=bci_fn,         args=bci_args,      name="Acquisition"),
#         Process(target=run_fft_window, args=(fft_queue,),  name="FFT_Graph"),
#     ]

#     try:
#         for p in procs:
#             p.start()

#         while procs[0].is_alive():
#             time.sleep(1.0)
#             if not procs[1].is_alive():
#                 print("BŁĄD: Proces akwizycji zakończył się nieoczekiwanie.")
#                 break

#     except KeyboardInterrupt:
#         print("\nPrzerwano.")
#     finally:
#         for p in procs:
#             if p.is_alive():
#                 p.terminate()
#                 p.join(timeout=3)
#         print("System wyłączony.")


# if __name__ == "__main__":
#     freeze_support()
#     main()