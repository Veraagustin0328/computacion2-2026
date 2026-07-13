import time
import os
import multiprocessing
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids, leer_stat, leer_status, leer_archivo

def leer_memoria_status(pid):
    """Lee los campos de memoria de /proc/<pid>/status."""
    status = leer_status(pid)
    if not status:
        return None

    def kb(campo):
        val = status.get(campo, "0 kB")
        try:
            return int(val.split()[0])
        except (ValueError, IndexError):
            return 0

    return {
        "vm_size": kb("VmSize"),
        "vm_rss": kb("VmRSS"),
        "vm_data": kb("VmData"),
        "vm_stk": kb("VmStk"),
        "vm_exe": kb("VmExe"),
        "vm_lib": kb("VmLib"),
        "vm_hwm": kb("VmHWM"),
        "vm_swap": kb("VmSwap"),
    }

def leer_page_faults(pid):
    """Lee minor y major page faults de /proc/<pid>/stat."""
    stat = leer_stat(pid)
    if not stat:
        return 0, 0
    try:
        # campos 10, 11, 12, 13 son minflt, cminflt, majflt, cmajflt
        minflt = int(stat[9])
        majflt = int(stat[11])
        return minflt, majflt
    except (IndexError, ValueError):
        return 0, 0

def leer_segmentos_maps(pid):
    """
    Lee /proc/<pid>/maps y agrupa los segmentos por tipo.
    Cada linea tiene: direccion permisos offset dev inode nombre
    """
    contenido = leer_archivo(f'/proc/{pid}/maps')
    if not contenido:
        return {}

    segmentos = {
        "text": 0,
        "data": 0,
        "heap": 0,
        "stack": 0,
        "shared": 0,
        "otros": 0,
    }

    for linea in contenido.splitlines():
        partes = linea.split()
        if len(partes) < 5:
            continue

        # calculo el tamaño del segmento a partir del rango de direcciones
        rango = partes[0]
        try:
            inicio, fin = rango.split('-')
            tamanio = (int(fin, 16) - int(inicio, 16)) // 1024  # en KB
        except ValueError:
            continue

        permisos = partes[1] if len(partes) > 1 else ""
        nombre = partes[-1] if len(partes) > 5 else ""

        if "[heap]" in nombre:
            segmentos["heap"] += tamanio
        elif "[stack]" in nombre:
            segmentos["stack"] += tamanio
        elif "r-xp" in permisos:
            # ejecutable de solo lectura = codigo (text)
            segmentos["text"] += tamanio
        elif "rw-p" in permisos:
            segmentos["data"] += tamanio
        elif "r--s" in permisos or "rw-s" in permisos:
            segmentos["shared"] += tamanio
        else:
            segmentos["otros"] += tamanio

    return segmentos

def analizar_memoria(pid):
    """Junta toda la info de memoria de un proceso."""
    mem = leer_memoria_status(pid)
    if not mem:
        return None

    minflt, majflt = leer_page_faults(pid)
    segmentos = leer_segmentos_maps(pid)

    return {
        "pid": pid,
        **mem,
        "minor_faults": minflt,
        "major_faults": majflt,
        "segmentos": segmentos,
    }

def analizador_memoria(queue_entrada, snapshot, intervalo_val):
    """Proceso analizador de memoria."""
    print(f"[Memoria] Iniciando, PID={multiprocessing.current_process().pid}")

    while True:
        try:
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            resultados = {}
            for pid in pids:
                datos = analizar_memoria(pid)
                if datos:
                    resultados[pid] = datos

            snapshot["memoria"] = {
                "datos": resultados,
                "timestamp": time.time(),
            }

            print(f"[Memoria] Analice {len(resultados)} procesos")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[Memoria] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 3.0)

        p = multiprocessing.Process(
            target=analizador_memoria,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        pids = listar_pids()
        for _ in range(2):
            q.put(pids)
            time.sleep(3)

        p.terminate()
        p.join()

        print("\nSnapshot de memoria:")
        if "memoria" in snapshot:
            datos = snapshot["memoria"]["datos"]
            for pid, info in list(datos.items())[:5]:
                print(f"  PID {pid}: VmRSS={info['vm_rss']}KB VmSize={info['vm_size']}KB heap={info['segmentos'].get('heap', 0)}KB")