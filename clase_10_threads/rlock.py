# rlock.py - RLock para locks reentrantes
# Agustin Vera - Computacion II 2026

import threading

rlock = threading.RLock()
contador = 0

def operacion_externa():
    with rlock:
        print(f"[Externa] Lock adquirido")
        operacion_interna()
        print(f"[Externa] Lock liberado")

def operacion_interna():
    # con Lock normal esto causaria deadlock
    # con RLock el mismo thread puede adquirirlo de nuevo
    with rlock:
        global contador
        contador += 1
        print(f"[Interna] contador={contador}")

if __name__ == "__main__":
    threads = [threading.Thread(target=operacion_externa) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Contador final: {contador}")
