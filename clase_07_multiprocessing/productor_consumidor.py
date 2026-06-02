from multiprocessing import Process, Queue
import time
import random

def productor(queue):
    for i in range(10):
        item = f"item_{i}"
        queue.put(item)
        print(f"[PRODUCTOR] Produjo: {item}")
        time.sleep(random.uniform(0.1, 0.3))
    queue.put(None)  # señal de fin
    print("[PRODUCTOR] Terminado")

def consumidor(queue):
    while True:
        item = queue.get()
        if item is None:
            break
        print(f"[CONSUMIDOR] Procesando: {item}")
        time.sleep(random.uniform(0.1, 0.4))
    print("[CONSUMIDOR] Terminado")

if __name__ == "__main__":
    queue = Queue()

    p_prod = Process(target=productor, args=(queue,))
    p_cons = Process(target=consumidor, args=(queue,))

    p_cons.start()
    p_prod.start()

    p_prod.join()
    p_cons.join()

    print("Todo terminado")
