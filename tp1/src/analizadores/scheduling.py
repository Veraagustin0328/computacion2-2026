import time
import multiprocessing
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids, leer_stat, leer_status

# politicas de scheduling segun el kernel
POLITICAS = {
    0: "SCHED_OTHER",
    1: "SCHED_FIFO",
    2: "SCHED_RR",
    3: "SCHED_BATCH",
    5: "SCHED_IDLE",
    6: "SCHED_DEADLINE",
}

def analizar_scheduling(pid):
    """Lee los datos de scheduling de un proceso."""
    stat = leer_stat(pid)
    status = leer_status(pid)

    if not stat or not status:
        return None

    try:
        # campo 18 es priority, campo 19 es nice
        priority = int(stat[17])
        nice = int(stat[18])

        # campo 41 es la politica de scheduling (en kernels modernos)
        politica_num = int(stat[40]) if len(stat) > 40 else 0
        politica = POLITICAS.get(politica_num, f"UNKNOWN({politica_num})")

        # campo 40 es rt_priority
        rt_priority = int(stat[39]) if len(stat) > 39 else 0

        # context switches del status
        vol = int(status.get("voluntary_ctxt_switches", "0"))
        invol = int(status.get("nonvoluntary_ctxt_switches", "0"))

        # cpu affinity
        affinity = status.get("Cpus_allowed_list", "0-?")

        # tiempo en modo usuario y kernel
        utime = int(stat[13])
        stime = int(stat[14])

        # SID y PGID del stat
        pgid = int(stat[4])
        sid = int(stat[5])

        return {
            "pid": pid,
            "nice": nice,
            "priority": priority,
            "politica": politica,
            "rt_priority": rt_priority,
            "ctx_voluntarios": vol,
            "ctx_involuntarios": invol,
            "cpu_affinity": affinity,
            "utime": utime,
            "stime": stime,
            "pgid": pgid,
            "sid": sid,
        }

    except (IndexError, ValueError) as e:
        return None

def analizador_scheduling(queue_entrada, snapshot, intervalo_val):
    """Proceso analizador de scheduling."""
    print(f"[Scheduling] Iniciando, PID={multiprocessing.current_process().pid}")

    while True:
        try:
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            resultados = {}
            for pid in pids:
                datos = analizar_scheduling(pid)
                if datos:
                    resultados[pid] = datos

            snapshot["scheduling"] = {
                "datos": resultados,
                "timestamp": time.time(),
            }

            print(f"[Scheduling] Analice {len(resultados)} procesos")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[Scheduling] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 10.0)

        p = multiprocessing.Process(
            target=analizador_scheduling,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        pids = listar_pids()
        q.put(pids)
        time.sleep(3)

        p.terminate()
        p.join()

        print("\nSnapshot de scheduling:")
        if "scheduling" in snapshot:
            datos = snapshot["scheduling"]["datos"]
            for pid, info in list(datos.items())[:5]:
                print(f"  PID {pid}: nice={info['nice']} | priority={info['priority']} | politica={info['politica']} | ctx_vol={info['ctx_voluntarios']} | ctx_invol={info['ctx_involuntarios']}")