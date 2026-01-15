import pyautogui
from config import STIMULI_MAP

class MouseController:
    def __init__(self, step=50):
        """
        step: liczba pikseli, o którą przesunie się kursor w jednym kroku
        """
        self.step = step
        # Wyłączenie "fail-safe" (opcjonalnie), aby kursor nie blokował się 
        # w rogu ekranu, choć w BCI lepiej zostawić to włączone dla bezpieczeństwa.
        pyautogui.FAILSAFE = True
        
        # Pobranie rozdzielczości ekranu dla ewentualnych ograniczeń
        self.screen_width, self.screen_height = pyautogui.size()

    def execute(self, command):
        """
        Wykonuje akcję na podstawie komendy otrzymanej z klasyfikatora.
        Zgodnie z Twoją pracą: góra, dół, lewo, prawo, kliknięcie.
        """
        if command == "UP":
            pyautogui.moveRel(0, -self.step, duration=0.2)
        
        elif command == "DOWN":
            pyautogui.moveRel(0, self.step, duration=0.2)
            
        elif command == "LEFT":
            pyautogui.moveRel(-self.step, 0, duration=0.2)
            
        elif command == "RIGHT":
            pyautogui.moveRel(self.step, 0, duration=0.2)
            
        elif command == "CLICK":
            pyautogui.click()
            print(">>> Symulacja kliknięcia myszy <<<")

    def get_position(self):
        return pyautogui.position()