from multiprocessing import Process, set_start_method
import time

def tarea():
    pass

def medir_metodo(metodo, n=100):
    set_start_method(metodo, force=True)
    inicio = time.time()

    procesos = []
    for _ in range(n):
        p = Process(target=tarea)
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    duracion = time.time() - inicio
    print(f"[{metodo}] {n} procesos en {duracion:.3f}s")

if __name__ == "__main__":
    medir_metodo("fork")
    medir_metodo("spawn")
