import threading
import time

# version SIN lock - tiene race condition
contador_sin_lock = 0

def incrementar_sin_lock(n):
    global contador_sin_lock
    for _ in range(n):
        temp = contador_sin_lock
        time.sleep(0)  # fuerza cambio de contexto
        contador_sin_lock = temp + 1
# version CON lock
contador_con_lock = 0
lock = threading.Lock()

def incrementar_con_lock(n):
    global contador_con_lock
    for _ in range(n):
        with lock:
            contador_con_lock += 1

def correr_test(func, nombre, n_threads, n_incrementos):
    threads = [threading.Thread(target=func, args=(n_incrementos,)) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

N_THREADS = 4
N_INCREMENTOS = 100000
ESPERADO = N_THREADS * N_INCREMENTOS

if __name__ == "__main__":
    print(f"Esperado: {ESPERADO}")

    correr_test(incrementar_sin_lock, "sin lock", N_THREADS, N_INCREMENTOS)
    print(f"Sin lock:  {contador_sin_lock} (perdidos: {ESPERADO - contador_sin_lock})")

    correr_test(incrementar_con_lock, "con lock", N_THREADS, N_INCREMENTOS)
    print(f"Con lock:  {contador_con_lock} (perdidos: {ESPERADO - contador_con_lock})")
