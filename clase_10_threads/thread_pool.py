# thread_pool.py - uso de ThreadPoolExecutor
# Agustin Vera - Computacion II 2026

import concurrent.futures
import time
import random
import math

def tarea_pesada(n):
    time.sleep(random.uniform(0.1, 0.5))
    return sum(math.sqrt(i) for i in range(n))

if __name__ == "__main__":
    tareas = [100000] * 10

    print("=== Con ThreadPoolExecutor ===")
    inicio = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(tarea_pesada, tareas))
    print(f"Tiempo: {time.time() - inicio:.2f}s")
    print(f"Resultados: {[round(r, 0) for r in resultados[:3]]}...")

    print("\n=== Con submit y futures ===")
    inicio = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(tarea_pesada, n): n for n in tareas}
        for future in concurrent.futures.as_completed(futures):
            n = futures[future]
            resultado = future.result()
            print(f"  Tarea({n}) = {round(resultado, 0)}")
    print(f"Tiempo: {time.time() - inicio:.2f}s")
