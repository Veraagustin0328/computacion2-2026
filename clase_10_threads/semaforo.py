# semaforo.py - control de acceso con Semaphore
# Agustin Vera - Computacion II 2026

import threading
import time
import random

# simulamos una base de datos con max 3 conexiones simultaneas
MAX_CONEXIONES = 3
semaforo = threading.Semaphore(MAX_CONEXIONES)
conexiones_activas = 0
lock_contador = threading.Lock()

def usar_base_de_datos(worker_id):
    global conexiones_activas

    print(f"[Worker {worker_id}] Esperando conexion...")
    with semaforo:
        with lock_contador:
            conexiones_activas += 1
            print(f"[Worker {worker_id}] Conexion obtenida (activas: {conexiones_activas})")

        duracion = random.uniform(0.5, 2.0)
        time.sleep(duracion)

        with lock_contador:
            conexiones_activas -= 1
            print(f"[Worker {worker_id}] Conexion liberada (activas: {conexiones_activas})")

if __name__ == "__main__":
    N_WORKERS = 8
    threads = [threading.Thread(target=usar_base_de_datos, args=(i,)) for i in range(N_WORKERS)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print("Todos los workers terminaron")
