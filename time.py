import time
from pyautogui import moveRel

while True:
    moveRel(1, 0)  # Двигаем мышь на 1 пиксель
    moveRel(-1, 0)  # Возвращаем обратно
    time.sleep(30)  # Пауза 30 секунд
