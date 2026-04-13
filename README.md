# SSVEP-BCI System

System sterowania kursorem myszy oparty na interfejsie mózg-komputer (BCI), wykorzystujący potencjały SSVEP i analizę korelacji kanonicznej (CCA).

## Architektura systemu
* **Akwizycja**: Odbiór danych z OpenBCI Cyton (8 kanałów, 250 Hz) przez bibliotekę BrainFlow.
* **Przetwarzanie**: Filtracja pasmowa 1–40 Hz oraz notch 50 Hz w celu usunięcia zakłóceń.
* **Klasyfikacja**: Algorytm CCA analizujący korelację sygnału z kanałów potylicznych (O1, O2, Oz) z funkcjami sinus/cosinus częstotliwości wzorcowych.
* **Logika**: Decyzja podejmowana jest po przekroczeniu progu korelacji i uzyskaniu stabilności w określonej liczbie okien czasowych.

## Struktura plików
* `main.py`: Zarządzanie procesami stymulacji i akwizycji.
* `config.py`: Parametry sprzętowe, port COM oraz mapowanie częstotliwości (6.66Hz - 12Hz).
* `modules/acquisition/cyton_board.py`: Pętla przetwarzania danych w czasie rzeczywistym i kontrola myszy.
* `modules/processing/`:
    * `signal_utils.py`: Funkcje do filtracji i analizy widmowej.
    * `classifier.py`: Implementacja logiki klasyfikatora.

## Konfiguracja klasyfikacji
THRESHOLD: Próg korelacji CCA (sugerowany zakres 0.3 - 0.4).

REQUIRED_STABILITY: Liczba powtórzeń wymagana do wykonania akcji.
