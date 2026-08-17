# condition.py - sincronizacion con Condition
# Agustin Vera - Computacion II 2026

import threading
import time
import random

buffer = []
MAX_BUFFER = 5
condition = threading.Condition()

def productor():
    for i in range(10):
        with condition:
            while len(buffer) >= MAX_BUFFER:
                print("[Productor] Buffer lleno, esperando...")
                condition.wait()
            buffer.append(f"item_{i}")
            print(f"[Productor] Agrego item_{i} (buffer: {len(buffer)})")
            condition.notify_all()
        time.sleep(random.uniform(0.1, 0.3))
    print("[Productor] Terminado")

def consumidor(consumidor_id):
    consumidos = 0
    while consumidos < 5:
        with condition:
            while not buffer:
                condition.wait()
            item = buffer.pop(0)
            consumidos += 1
            print(f"[Consumidor {consumidor_id}] Consumio {item} (buffer: {len(buffer)})")
            condition.notify_all()
        time.sleep(random.uniform(0.2, 0.5))

if __name__ == "__main__":
    prod = threading.Thread(target=productor)
    cons = [threading.Thread(target=consumidor, args=(i,)) for i in range(2)]

    for c in cons:
        c.start()
    prod.start()

    prod.join()
    for c in cons:
        c.join()

    print("Todo terminado")
