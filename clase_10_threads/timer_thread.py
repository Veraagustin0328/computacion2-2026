# timer_thread.py - threads temporizados con Timer
# Agustin Vera - Computacion II 2026

import threading
import time

def tarea_programada(nombre):
    print(f"[{nombre}] Ejecutando a las {time.strftime('%H:%M:%S')}")

def tarea_periodica(nombre, intervalo, repeticiones, contador=[0]):
    contador[0] += 1
    print(f"[{nombre}] Ejecucion {contador[0]} a las {time.strftime('%H:%M:%S')}")
    if contador[0] < repeticiones:
        t = threading.Timer(intervalo, tarea_periodica, args=[nombre, intervalo, repeticiones, contador])
        t.start()

if __name__ == "__main__":
    print(f"Iniciando a las {time.strftime('%H:%M:%S')}")

    t1 = threading.Timer(1.0, tarea_programada, args=["Timer-1seg"])
    t2 = threading.Timer(2.0, tarea_programada, args=["Timer-2seg"])
    t3 = threading.Timer(3.0, tarea_programada, args=["Timer-3seg"])

    t1.start()
    t2.start()
    t3.start()

    tarea_periodica("Periodico", 1.0, 4, [0])

    t1.join()
    t2.join()
    t3.join()
    time.sleep(5)
    print("Todo terminado")
