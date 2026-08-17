# primer_thread.py - primer contacto con threading
# Agustin Vera - Computacion II 2026

import threading
import time
import os

def tarea(nombre, duracion):
    print(f"[{nombre}] Iniciando, TID={threading.get_ident()}, PID={os.getpid()}")
    time.sleep(duracion)
    print(f"[{nombre}] Terminado despues de {duracion}s")

if __name__ == "__main__":
    print(f"[Main] PID={os.getpid()}, TID={threading.get_ident()}")

    t1 = threading.Thread(target=tarea, args=("Thread-1", 2))
    t2 = threading.Thread(target=tarea, args=("Thread-2", 1))
    t3 = threading.Thread(target=tarea, args=("Thread-3", 3))

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    print("[Main] Todos los threads terminaron")
