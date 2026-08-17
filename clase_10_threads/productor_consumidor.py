# productor_consumidor.py - patron productor consumidor con Queue
# Agustin Vera - Computacion II 2026

import threading
import queue
import time
import random

def productor(q, n_items):
    for i in range(n_items):
        item = f"item_{i}"
        q.put(item)
        print(f"[Productor] Produjo: {item} (queue size: {q.qsize()})")
        time.sleep(random.uniform(0.1, 0.3))
    q.put(None)  # señal de fin
    print("[Productor] Terminado")

def consumidor(q, consumidor_id):
    while True:
        item = q.get()
        if item is None:
            q.put(None)  # reenviar señal para otros consumidores
            break
        print(f"[Consumidor {consumidor_id}] Procesando: {item}")
        time.sleep(random.uniform(0.2, 0.5))
        q.task_done()
    print(f"[Consumidor {consumidor_id}] Terminado")

if __name__ == "__main__":
    q = queue.Queue(maxsize=5)

    prod = threading.Thread(target=productor, args=(q, 10))
    consumidores = [threading.Thread(target=consumidor, args=(q, i)) for i in range(3)]

    for c in consumidores:
        c.start()
    prod.start()

    prod.join()
    for c in consumidores:
        c.join()

    print("Todo terminado")
