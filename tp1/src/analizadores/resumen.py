import time
import os
import multiprocessing
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids, leer_stat, leer_status, leer_cmdline

# cuantos jiffies hay por segundo en este sistema
HZ = os.sysconf('SC_CLK_TCK')

def calcular_cpu(pid, jiffies_anteriores, tiempo_anterior):
    """
    Calcula el CPU% de un proceso comparando dos lecturas de jiffies.
    Retorna (cpu_porcentaje, jiffies_actuales, tiempo_actual)
    """
    stat = leer_stat(pid)
    if not stat:
        return 0.0, 0, time.time()

    try:
        # campos 14 y 15 son utime y stime (tiempo en modo usuario y kernel)
        utime = int(stat[13])
        stime = int(stat[14])
        jiffies_actuales = utime + stime
        tiempo_actual = time.time()

        if tiempo_anterior is None or jiffies_anteriores is None:
            return 0.0, jiffies_actuales, tiempo_actual

        delta_jiffies = jiffies_actuales - jiffies_anteriores
        delta_tiempo = tiempo_actual - tiempo_anterior

        if delta_tiempo <= 0:
            return 0.0, jiffies_actuales, tiempo_actual

        cpu = (delta_jiffies / HZ) / delta_tiempo * 100
        return round(cpu, 1), jiffies_actuales, tiempo_actual

    except (IndexError, ValueError):
        return 0.0, 0, time.time()

def analizar_proceso(pid, jiffies_ant=None, tiempo_ant=None):
    """Extrae todos los datos basicos de un proceso."""
    stat = leer_stat(pid)
    status = leer_status(pid)
    cmdline = leer_cmdline(pid)

    if not stat or not status:
        return None

    cpu, jiffies, tiempo = calcular_cpu(pid, jiffies_ant, tiempo_ant)

    try:
        return {
            "pid": pid,
            "nombre": stat[1],
            "estado": stat[2],
            "ppid": int(stat[3]),
            "cpu_pct": cpu,
            "rss_kb": int(status.get("VmRSS", "0 kB").split()[0]),
            "threads": int(status.get("Threads", "1")),
            "uid": status.get("Uid", "0").split()[0],
            "cmdline": cmdline or stat[1],
            "_jiffies": jiffies,
            "_tiempo": tiempo,
        }
    except (ValueError, IndexError):
        return None

def analizador_resumen(queue_entrada, snapshot, intervalo_val, intervalo=2):
    """
    Proceso analizador de resumen.
    Lee PIDs de la cola, analiza cada uno y actualiza el snapshot.
    """
    print(f"[Resumen] Iniciando, PID={multiprocessing.current_process().pid}")

    # cache de jiffies anteriores para calcular CPU%
    cache_jiffies = {}

    while True:
        try:
            # espero a que el recolector me mande los PIDs
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            resultados = {}
            for pid in pids:
                ant = cache_jiffies.get(pid)
                jiffies_ant = ant["jiffies"] if ant else None
                tiempo_ant = ant["tiempo"] if ant else None

                datos = analizar_proceso(pid, jiffies_ant, tiempo_ant)
                if datos:
                    resultados[pid] = datos
                    cache_jiffies[pid] = {
                        "jiffies": datos["_jiffies"],
                        "tiempo": datos["_tiempo"],
                    }

            # limpio PIDs que ya no existen
            cache_jiffies = {p: v for p, v in cache_jiffies.items() if p in pids}

            # actualizo el snapshot compartido
            snapshot["resumen"] = {
                "datos": resultados,
                "timestamp": time.time(),
            }

            print(f"[Resumen] Analice {len(resultados)} procesos")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[Resumen] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 2.0)

        p = multiprocessing.Process(
            target=analizador_resumen,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        # simulo el recolector mandando PIDs
        pids = listar_pids()
        for _ in range(3):
            q.put(pids)
            time.sleep(2)

        p.terminate()
        p.join()

        print("\nSnapshot final:")
        if "resumen" in snapshot:
            datos = snapshot["resumen"]["datos"]
            for pid, info in list(datos.items())[:5]:
                print(f"  PID {pid}: {info['nombre']} | {info['estado']} | CPU: {info['cpu_pct']}% | RSS: {info['rss_kb']}KB")
                
                