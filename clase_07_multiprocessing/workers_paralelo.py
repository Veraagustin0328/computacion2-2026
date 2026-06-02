from multiprocessing import Process
import random
import time
import os

def worker(worker_id):
    espera = random.uniform(0.5, 2.0)
    print(f"[Worker {worker_id}] Esperando {espera:.2f}s...")
    time.sleep(espera)
    print(f"[Worker {worker_id}] Terminado")

if __name__ == "__main__":
    inicio = time.time()

    procesos = []
    for i in range(5):
        p = Process(target=worker, args=(i,))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    duracion = time.time() - inicio
    print(f"\nTodos los workers terminaron en {duracion:.2f}s")
