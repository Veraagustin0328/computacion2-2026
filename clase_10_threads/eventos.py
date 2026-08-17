# evento.py - coordinacion con Event
# Agustin Vera - Computacion II 2026

import threading
import time
import random

evento_datos_listos = threading.Event()
datos_compartidos = []

def productor():
    print("[Productor] Preparando datos...")
    time.sleep(2)
    datos_compartidos.extend([1, 2, 3, 4, 5])
    print("[Productor] Datos listos, notificando consumidores")
    evento_datos_listos.set()

def consumidor(consumidor_id):
    print(f"[Consumidor {consumidor_id}] Esperando datos...")
    evento_datos_listos.wait()
    print(f"[Consumidor {consumidor_id}] Datos recibidos: {datos_compartidos}")

if __name__ == "__main__":
    consumidores = [threading.Thread(target=consumidor, args=(i,)) for i in range(4)]
    prod = threading.Thread(target=productor)

    for c in consumidores:
        c.start()
    prod.start()

    prod.join()
    for c in consumidores:
        c.join()

    print("Todo terminado")
