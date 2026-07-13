import time
import multiprocessing
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids, leer_archivo, leer_stat

# para calcular CPU global necesitamos dos lecturas
_jiffies_anteriores = None
_tiempo_anterior = None

def leer_cpu_global():
    """Lee /proc/stat y calcula el uso de CPU global."""
    global _jiffies_anteriores, _tiempo_anterior

    contenido = leer_archivo('/proc/stat')
    if not contenido:
        return {}

    linea_cpu = contenido.splitlines()[0]
    campos = linea_cpu.split()

    # campos: cpu user nice system idle iowait irq softirq steal
    try:
        user = int(campos[1])
        nice = int(campos[2])
        system = int(campos[3])
        idle = int(campos[4])
        iowait = int(campos[5])
        irq = int(campos[6])
        softirq = int(campos[7])

        total = user + nice + system + idle + iowait + irq + softirq
        activo = total - idle

        if _jiffies_anteriores is None:
            _jiffies_anteriores = {"total": total, "activo": activo}
            _tiempo_anterior = time.time()
            return {"user": 0, "system": 0, "idle": 100, "iowait": 0}

        delta_total = total - _jiffies_anteriores["total"]
        delta_activo = activo - _jiffies_anteriores["activo"]
        delta_idle = delta_total - delta_activo

        if delta_total == 0:
            return {"user": 0, "system": 0, "idle": 100, "iowait": 0}

        cpu_user = round((user - _jiffies_anteriores.get("user", user)) / delta_total * 100, 1) if "user" in _jiffies_anteriores else 0
        cpu_system = round((system - _jiffies_anteriores.get("system", system)) / delta_total * 100, 1) if "system" in _jiffies_anteriores else 0
        cpu_idle = round(delta_idle / delta_total * 100, 1)
        cpu_iowait = round((iowait - _jiffies_anteriores.get("iowait", iowait)) / delta_total * 100, 1) if "iowait" in _jiffies_anteriores else 0

        _jiffies_anteriores = {
            "total": total, "activo": activo,
            "user": user, "system": system, "iowait": iowait
        }

        return {
            "user": cpu_user,
            "system": cpu_system,
            "idle": cpu_idle,
            "iowait": cpu_iowait,
            "total_pct": round(delta_activo / delta_total * 100, 1),
        }

    except (IndexError, ValueError):
        return {}

def leer_memoria_global():
    """Lee /proc/meminfo y retorna los datos de memoria del sistema."""
    contenido = leer_archivo('/proc/meminfo')
    if not contenido:
        return {}

    mem = {}
    for linea in contenido.splitlines():
        if ':' in linea:
            clave, valor = linea.split(':', 1)
            try:
                mem[clave.strip()] = int(valor.strip().split()[0])
            except (ValueError, IndexError):
                pass

    return {
        "total_kb": mem.get("MemTotal", 0),
        "libre_kb": mem.get("MemFree", 0),
        "disponible_kb": mem.get("MemAvailable", 0),
        "buffers_kb": mem.get("Buffers", 0),
        "cached_kb": mem.get("Cached", 0),
        "swap_total_kb": mem.get("SwapTotal", 0),
        "swap_libre_kb": mem.get("SwapFree", 0),
        "usado_kb": mem.get("MemTotal", 0) - mem.get("MemAvailable", 0),
    }

def leer_loadavg():
    """Lee /proc/loadavg."""
    contenido = leer_archivo('/proc/loadavg')
    if not contenido:
        return {}
    campos = contenido.split()
    try:
        return {
            "1min": float(campos[0]),
            "5min": float(campos[1]),
            "15min": float(campos[2]),
        }
    except (IndexError, ValueError):
        return {}

def contar_procesos(pids):
    """Cuenta procesos por estado y totales."""
    estados = {}
    zombies = 0
    threads_total = 0

    for pid in pids:
        stat = leer_stat(pid)
        if not stat:
            continue
        estado = stat[2]
        estados[estado] = estados.get(estado, 0) + 1
        if estado == 'Z':
            zombies += 1

    return {
        "total": len(pids),
        "por_estado": estados,
        "zombies": zombies,
    }

def analizar_sistema(pids):
    """Junta todas las estadisticas globales."""
    return {
        "cpu": leer_cpu_global(),
        "memoria": leer_memoria_global(),
        "loadavg": leer_loadavg(),
        "procesos": contar_procesos(pids),
    }

def analizador_sistema(queue_entrada, snapshot, intervalo_val):
    """Proceso analizador de estadisticas globales."""
    print(f"[Sistema] Iniciando, PID={multiprocessing.current_process().pid}")

    while True:
        try:
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            datos = analizar_sistema(pids)
            snapshot["sistema"] = {
                "datos": datos,
                "timestamp": time.time(),
            }

            print(f"[Sistema] CPU: {datos['cpu'].get('total_pct', 0)}% | RAM usada: {datos['memoria'].get('usado_kb', 0) // 1024}MB | Load: {datos['loadavg'].get('1min', 0)}")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[Sistema] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 2.0)

        p = multiprocessing.Process(
            target=analizador_sistema,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        pids = listar_pids()
        for _ in range(3):
            q.put(pids)
            time.sleep(2)

        p.terminate()
        p.join()

        print("\nSnapshot del sistema:")
        if "sistema" in snapshot:
            datos = snapshot["sistema"]["datos"]
            mem = datos["memoria"]
            print(f"  CPU total: {datos['cpu'].get('total_pct', 0)}%")
            print(f"  RAM: {mem['usado_kb']//1024}MB usados de {mem['total_kb']//1024}MB")
            print(f"  Load avg: {datos['loadavg']}")
            print(f"  Procesos: {datos['procesos']}")