import os
import time
import multiprocessing
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids

def inferir_tipo(destino):
    """Infiere el tipo de FD a partir del destino del symlink."""
    if destino.startswith("socket:"):
        return "socket"
    elif destino.startswith("pipe:"):
        return "pipe"
    elif destino.startswith("/dev/pts"):
        return "tty"
    elif destino.startswith("/dev/"):
        return "dispositivo"
    elif destino == "/dev/null":
        return "null"
    elif destino.startswith("/"):
        return "archivo"
    elif destino.startswith("anon_inode:"):
        return "anon"
    else:
        return "otro"

def leer_fds(pid):
    """Lee todos los FDs abiertos de un proceso."""
    fd_dir = f'/proc/{pid}/fd'
    try:
        fds = []
        for fd in os.listdir(fd_dir):
            try:
                destino = os.readlink(f'{fd_dir}/{fd}')
                fds.append({
                    "fd": int(fd),
                    "destino": destino,
                    "tipo": inferir_tipo(destino),
                })
            except (PermissionError, FileNotFoundError):
                continue
        return sorted(fds, key=lambda x: x["fd"])
    except (PermissionError, FileNotFoundError):
        return []

def analizar_fds(pid):
    """Junta toda la info de FDs de un proceso."""
    fds = leer_fds(pid)
    if fds is None:
        return None

    # cuento cuantos hay de cada tipo
    conteo_tipos = {}
    for fd in fds:
        tipo = fd["tipo"]
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1

    return {
        "pid": pid,
        "total": len(fds),
        "fds": fds,
        "tipos": conteo_tipos,
    }

def analizador_fds(queue_entrada, snapshot, intervalo_val):
    """Proceso analizador de file descriptors."""
    print(f"[FDs] Iniciando, PID={multiprocessing.current_process().pid}")

    while True:
        try:
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            resultados = {}
            for pid in pids:
                datos = analizar_fds(pid)
                if datos:
                    resultados[pid] = datos

            snapshot["fds"] = {
                "datos": resultados,
                "timestamp": time.time(),
            }

            print(f"[FDs] Analice {len(resultados)} procesos")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[FDs] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 5.0)

        p = multiprocessing.Process(
            target=analizador_fds,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        pids = listar_pids()
        q.put(pids)
        time.sleep(5)

        p.terminate()
        p.join()

        print("\nSnapshot de FDs:")
        if "fds" in snapshot:
            datos = snapshot["fds"]["datos"]
            for pid, info in list(datos.items())[:5]:
                print(f"  PID {pid}: {info['total']} FDs abiertos | tipos: {info['tipos']}")