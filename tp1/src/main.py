import multiprocessing
import signal
import time
import sys
import os

# agrego src al path para los imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recolector import recolector
from analizadores.resumen import analizador_resumen
from analizadores.memoria import analizador_memoria
from analizadores.fds import analizador_fds
from analizadores.threads import analizador_threads
from analizadores.senales import analizador_señales
from analizadores.scheduling import analizador_scheduling
from analizadores.sistema import analizador_sistema

def crear_snapshot_inicial(manager):
    """Crea el snapshot compartido con valores iniciales."""
    snapshot = manager.dict()
    snapshot["resumen"] = {"datos": {}, "timestamp": 0}
    snapshot["memoria"] = {"datos": {}, "timestamp": 0}
    snapshot["fds"] = {"datos": {}, "timestamp": 0}
    snapshot["threads"] = {"datos": {}, "timestamp": 0}
    snapshot["senales"] = {"datos": {}, "timestamp": 0}
    snapshot["scheduling"] = {"datos": {}, "timestamp": 0}
    snapshot["sistema"] = {"datos": {}, "timestamp": 0}
    return snapshot

def crear_intervalos(manager):
    """Crea los valores compartidos para los intervalos de cada analizador."""
    return {
        "resumen":    multiprocessing.Value('d', 2.0),
        "memoria":    multiprocessing.Value('d', 3.0),
        "fds":        multiprocessing.Value('d', 5.0),
        "threads":    multiprocessing.Value('d', 2.0),
        "senales":    multiprocessing.Value('d', 10.0),
        "scheduling": multiprocessing.Value('d', 10.0),
        "sistema":    multiprocessing.Value('d', 2.0),
    }

def crear_queues():
    """Crea una cola por cada analizador."""
    return {
        "resumen":    multiprocessing.Queue(maxsize=2),
        "memoria":    multiprocessing.Queue(maxsize=2),
        "fds":        multiprocessing.Queue(maxsize=2),
        "threads":    multiprocessing.Queue(maxsize=2),
        "senales":    multiprocessing.Queue(maxsize=2),
        "scheduling": multiprocessing.Queue(maxsize=2),
        "sistema":    multiprocessing.Queue(maxsize=2),
    }

def iniciar_analizadores(queues, snapshot, intervalos):
    """Arranca los 7 analizadores como procesos independientes."""
    procesos = []

    configs = [
        ("resumen",    analizador_resumen,    (queues["resumen"],    snapshot, intervalos["resumen"])),
        ("memoria",    analizador_memoria,    (queues["memoria"],    snapshot, intervalos["memoria"])),
        ("fds",        analizador_fds,        (queues["fds"],        snapshot, intervalos["fds"])),
        ("threads",    analizador_threads,    (queues["threads"],    snapshot, intervalos["threads"])),
        ("senales",    analizador_señales,    (queues["senales"],    snapshot, intervalos["senales"])),
        ("scheduling", analizador_scheduling, (queues["scheduling"], snapshot, intervalos["scheduling"])),
        ("sistema",    analizador_sistema,    (queues["sistema"],    snapshot, intervalos["sistema"])),
    ]

    for nombre, funcion, args in configs:
        p = multiprocessing.Process(
            target=funcion,
            args=args,
            name=f"analizador_{nombre}",
            daemon=True
        )
        p.start()
        procesos.append(p)
        print(f"[Main] Analizador '{nombre}' iniciado (PID {p.pid})")

    return procesos

def shutdown(procesos_analizadores, proceso_recolector):
    """Termina todos los procesos limpiamente."""
    print("\n[Main] Iniciando shutdown...")

    for p in procesos_analizadores:
        if p.is_alive():
            p.terminate()

    if proceso_recolector.is_alive():
        proceso_recolector.terminate()

    for p in procesos_analizadores:
        p.join(timeout=3)

    proceso_recolector.join(timeout=3)
    print("[Main] Todos los procesos terminados")

def main():
    print("[Main] Iniciando monitor de procesos...")
    print(f"[Main] PID principal: {os.getpid()}")

    with multiprocessing.Manager() as manager:
        # crear estructuras compartidas
        snapshot = crear_snapshot_inicial(manager)
        intervalos = crear_intervalos(manager)
        queues = crear_queues()

        # arrancar analizadores
        procesos_analizadores = iniciar_analizadores(queues, snapshot, intervalos)

        # arrancar recolector
        proceso_recolector = multiprocessing.Process(
            target=recolector,
            args=(queues, 2),
            name="recolector",
            daemon=True
        )
        proceso_recolector.start()
        print(f"[Main] Recolector iniciado (PID {proceso_recolector.pid})")

        print("\n[Main] Sistema corriendo. Ctrl+C para salir.\n")

        try:
            # loop principal - por ahora solo muestra el snapshot cada 5s
            while True:
                time.sleep(5)
                if "sistema" in snapshot and snapshot["sistema"]["timestamp"] > 0:
                    datos = snapshot["sistema"]["datos"]
                    mem = datos.get("memoria", {})
                    cpu = datos.get("cpu", {})
                    procs = datos.get("procesos", {})
                    print(f"[Main] CPU: {cpu.get('total_pct', 0)}% | RAM: {mem.get('usado_kb', 0)//1024}MB | Procesos: {procs.get('total', 0)}")

        except KeyboardInterrupt:
            shutdown(procesos_analizadores, proceso_recolector)

if __name__ == "__main__":
    main()