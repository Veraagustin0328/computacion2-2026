import time
import multiprocessing
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procfs import listar_pids, leer_status

# mapa de numero de señal a nombre
SEÑALES = {
    1: "SIGHUP", 2: "SIGINT", 3: "SIGQUIT", 4: "SIGILL",
    5: "SIGTRAP", 6: "SIGABRT", 7: "SIGBUS", 8: "SIGFPE",
    9: "SIGKILL", 10: "SIGUSR1", 11: "SIGSEGV", 12: "SIGUSR2",
    13: "SIGPIPE", 14: "SIGALRM", 15: "SIGTERM", 16: "SIGSTKFLT",
    17: "SIGCHLD", 18: "SIGCONT", 19: "SIGSTOP", 20: "SIGTSTP",
    21: "SIGTTIN", 22: "SIGTTOU", 23: "SIGURG", 24: "SIGXCPU",
    25: "SIGXFSZ", 26: "SIGVTALRM", 27: "SIGPROF", 28: "SIGWINCH",
    29: "SIGIO", 30: "SIGPWR", 31: "SIGSYS",
}

def decodificar_mascara(hex_str):
    """
    Convierte una mascara hexadecimal de señales a lista de nombres.
    Cada bit en 1 indica que esa señal esta en la mascara.
    """
    try:
        mascara = int(hex_str, 16)
    except (ValueError, TypeError):
        return []

    señales_activas = []
    for bit in range(64):
        if mascara & (1 << bit):
            num_señal = bit + 1
            nombre = SEÑALES.get(num_señal, f"SIG{num_señal}")
            señales_activas.append(nombre)
    return señales_activas

def analizar_señales(pid):
    """Lee y decodifica las mascaras de señales de un proceso."""
    status = leer_status(pid)
    if not status:
        return None

    return {
        "pid": pid,
        "pendientes_proceso": decodificar_mascara(status.get("SigPnd", "0")),
        "pendientes_grupo": decodificar_mascara(status.get("ShdPnd", "0")),
        "bloqueadas": decodificar_mascara(status.get("SigBlk", "0")),
        "ignoradas": decodificar_mascara(status.get("SigIgn", "0")),
        "capturadas": decodificar_mascara(status.get("SigCgt", "0")),
        # guardo los valores hex tambien por si los necesito mostrar
        "SigBlk_hex": status.get("SigBlk", "0"),
        "SigIgn_hex": status.get("SigIgn", "0"),
        "SigCgt_hex": status.get("SigCgt", "0"),
    }

def analizador_señales(queue_entrada, snapshot, intervalo_val):
    """Proceso analizador de señales."""
    print(f"[Señales] Iniciando, PID={multiprocessing.current_process().pid}")

    while True:
        try:
            pids = queue_entrada.get(timeout=5)
            intervalo_actual = intervalo_val.value

            resultados = {}
            for pid in pids:
                datos = analizar_señales(pid)
                if datos:
                    resultados[pid] = datos

            snapshot["senales"] = {
                "datos": resultados,
                "timestamp": time.time(),
            }

            print(f"[Señales] Analice {len(resultados)} procesos")
            time.sleep(intervalo_actual)

        except Exception as e:
            if "Empty" in type(e).__name__:
                continue
            print(f"[Señales] Error: {e}")

if __name__ == "__main__":
    from multiprocessing import Queue, Manager, Value

    q = Queue()
    with Manager() as manager:
        snapshot = manager.dict()
        intervalo_val = Value('d', 10.0)

        p = multiprocessing.Process(
            target=analizador_señales,
            args=(q, snapshot, intervalo_val)
        )
        p.start()

        pids = listar_pids()
        q.put(pids)
        time.sleep(3)

        p.terminate()
        p.join()

        print("\nSnapshot de señales:")
        if "senales" in snapshot:
            datos = snapshot["senales"]["datos"]
            for pid, info in list(datos.items())[:5]:
                print(f"  PID {pid}:")
                print(f"    Bloqueadas: {info['bloqueadas']}")
                print(f"    Ignoradas:  {info['ignoradas']}")
                print(f"    Capturadas: {info['capturadas']}")