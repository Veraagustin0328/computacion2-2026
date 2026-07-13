import time
import multiprocessing
from procfs import listar_pids

def recolector(queues, intervalo=2):
    """
    Lee /proc cada 'intervalo' segundos y manda la lista de PIDs
    a todos los analizadores via sus respectivas colas.
    queues: diccionario con las colas de cada analizador
    """
    print(f"[Recolector] Iniciando, PID={multiprocessing.current_process().pid}")

    while True:
        try:
            pids = listar_pids()
            print(f"[Recolector] Encontre {len(pids)} procesos")

            # mando los PIDs a cada analizador
            for nombre, queue in queues.items():
                try:
                    # si la cola esta llena no bloqueo, simplemente descarto
                    queue.put_nowait(pids)
                except Exception:
                    pass

            time.sleep(intervalo)

        except KeyboardInterrupt:
            print("[Recolector] Terminando...")
            break

if __name__ == "__main__":
    # prueba simple con una sola cola
    q = multiprocessing.Queue()
    queues = {"test": q}

    # arranco el recolector en un proceso separado
    p = multiprocessing.Process(target=recolector, args=(queues, 2))
    p.start()

    # el proceso principal lee de la cola
    for _ in range(3):
        pids = q.get()
        print(f"[Main] Recibi {len(pids)} PIDs: {pids[:5]}...")

    p.terminate()
    p.join()
    print("[Main] Listo")