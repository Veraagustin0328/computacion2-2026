import os
import time
import multiprocessing
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids, leer_stat, leer_archivo

HZ = os.sysconf('SC_CLK_TCK')

def leer_threads(pid):
    """Lista todos los TIDs de un proceso."""
    try:
        return [int(t) for t in os.listdir(f'/proc/{pid}/task')]
    except (PermissionError, FileNotFoundError):
        return []

def leer_stat_thread(pid, tid):
    """Lee /proc/<pid>/task/<tid>/stat."""
    contenido = leer_archivo(f'/proc/{pid}/task/{tid}/stat')
    if not contenido:
        return None
    idx_inicio = contenido.find('(')
    idx_fin = contenido.rfind(')')
    nombre = contenido[idx_inicio+1:idx_fin]
    resto = contenido[idx_fin+2:].split()
    return [contenido[:idx_inicio].strip(), nombre] + resto

def leer_nombre_thread(pid, tid):
    """Lee el nombre del thread de /proc/<pid>/task/<tid>/comm."""
    contenido = leer_archivo(f'/proc/{pid}/task/{tid}/comm')
    return contenido.strip() if contenido else f"thread-{tid}"

def leer_ctx_switches_thread(pid, tid):
    """Lee los context switches del thread."""
    contenido = leer_archivo(f'/proc/{pid}/task/{tid}/status')
    if not contenido:
        return 0, 0
    voluntarios = 0
    involuntarios = 0
    for linea in contenido.splitlines():
        if 'voluntary_ctxt_switches' in linea and 'non' not in linea:
            try:
                voluntarios = int(linea.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif 'nonvoluntary_ctxt_switches' in linea:
            try:
                involuntarios = int(linea.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
    return voluntarios, involuntarios

def analizar_threads(pid, cache_jiffies=None):
    """Analiza todos los threads de un proceso."""
    tids = leer_threads(pid)
    if not tids:
        return None

    threads = []
    for tid in tids:
        stat = leer_stat_thread(pid, tid)
        if not stat:
            continue

        try:
            utime = int(stat[13])
            stime = int(stat[14])
            jiffies = utime + stime

            # calculo CPU% si tengo cache
            cpu = 0.0
            if cache_jiffies and tid in cache_jiffies:
                ant = cache_jiffies[tid]
                delta_j = jiffies - ant["jiffies"]
                delta_t = time.time() - ant["tiempo"]
                if delta_t > 0:
                    cpu = round((delta_j / HZ) / delta_t * 100, 1)

            vol, invol = leer_ctx_switches_thread(pid, tid)

            threads.append({
                "tid": tid,
                "nombre": leer_nombre_thread(pid, tid),
                "estado": stat[2],
                "cpu_pct": cpu,
                "utime": utime,
                "stime": stime,
                "_jiffies": jiffies,
                "_tiempo": time.time(),
                "ctx_voluntarios": vol,
                "ctx_involuntarios": invol,
            })
        except (IndexError, ValueError):
            continue

    return {
        "pid": pid,
        "total": len(threads),
        "threads": threads,
    }

def analizador_threads(queue_entrada, snapshot, intervalo_val):
    """Proceso analizador de threads."""
    print(f"[Threads] Iniciando, PID={multiprocessing.current_process().pid}")

    cache_jiffies = {}

    while True:
        try:
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            resultados = {}
            for pid in pids:
                datos = analizar_threads(pid, cache_jiffies.get(pid))
                if datos:
                    resultados[pid] = datos
                    # actualizo cache por TID
                    cache_jiffies[pid] = {
                        t["tid"]: {"jiffies": t["_jiffies"], "tiempo": t["_tiempo"]}
                        for t in datos["threads"]
                    }

            snapshot["threads"] = {
                "datos": resultados,
                "timestamp": time.time(),
            }

            print(f"[Threads] Analice {len(resultados)} procesos")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[Threads] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 2.0)

        p = multiprocessing.Process(
            target=analizador_threads,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        pids = listar_pids()
        for _ in range(2):
            q.put(pids)
            time.sleep(2)

        p.terminate()
        p.join()

        print("\nSnapshot de threads:")
        if "threads" in snapshot:
            datos = snapshot["threads"]["datos"]
            for pid, info in list(datos.items())[:5]:
                print(f"  PID {pid}: {info['total']} thread(s)")
                for t in info["threads"][:2]:
                    print(f"    TID {t['tid']}: {t['nombre']} | {t['estado']} | CPU: {t['cpu_pct']}%")