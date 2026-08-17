# gil_demo.py - demostracion del GIL y sus limitaciones
# Agustin Vera - Computacion II 2026

import threading
import time
import math

def tarea_cpu(n):
    """Tarea CPU-bound: calcula raices cuadradas."""
    return sum(math.sqrt(i) for i in range(n))

def medir(func, args, n_workers, nombre):
    inicio = time.time()
    workers = [threading.Thread(target=func, args=args) for _ in range(n_workers)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    duracion = time.time() - inicio
    print(f"{nombre}: {duracion:.2f}s")
    return duracion

N = 1_000_000
TAREAS = 4

if __name__ == "__main__":
    print("=== Tarea CPU-bound (GIL limita el paralelismo) ===")

    inicio = time.time()
    for _ in range(TAREAS):
        tarea_cpu(N)
    t_seq = time.time() - inicio
    print(f"Secuencial: {t_seq:.2f}s")

    t_par = medir(tarea_cpu, (N,), TAREAS, f"Threads ({TAREAS} workers)")

    print(f"Speedup real: {t_seq/t_par:.2f}x (esperado: {TAREAS}x)")
    print("-> El GIL impide paralelismo real en tareas CPU-bound")
