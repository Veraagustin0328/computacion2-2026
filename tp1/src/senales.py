import signal
import json
import time
import os

# flag global para el shutdown
_ejecutando = True
_verbose = False

def setup_señales(snapshot, intervalos):
    """Registra todos los handlers de señales del monitor."""

    def handler_shutdown(sig, frame):
        global _ejecutando
        nombre = signal.Signals(sig).name
        print(f"\n[Señales] Recibi {nombre}, iniciando shutdown limpio...")
        _ejecutando = False

    def handler_reload(sig, frame):
        """SIGHUP - recarga la configuracion desde config.json."""
        print("\n[Señales] SIGHUP - recargando configuracion...")
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config.json"
            )
            with open(config_path) as f:
                config = json.load(f)

            for vista, valor in config.get("intervalos", {}).items():
                if vista in intervalos:
                    intervalos[vista].value = float(valor)

            print(f"[Señales] Configuracion recargada: {config.get('intervalos', {})}")
        except Exception as e:
            print(f"[Señales] Error recargando config: {e}")

    def handler_dump(sig, frame):
        """SIGUSR1 - dump del snapshot actual a JSON."""
        timestamp = int(time.time())
        nombre_archivo = f"dump_{timestamp}.json"
        print(f"\n[Señales] SIGUSR1 - dumpeando snapshot a {nombre_archivo}...")
        try:
            # convertir el snapshot a dict serializable
            datos = {}
            for clave in snapshot.keys():
                try:
                    datos[clave] = dict(snapshot[clave])
                except Exception:
                    datos[clave] = str(snapshot[clave])

            with open(nombre_archivo, 'w') as f:
                json.dump(datos, f, indent=2, default=str)
            print(f"[Señales] Dump guardado en {nombre_archivo}")
        except Exception as e:
            print(f"[Señales] Error al dumpear: {e}")

    def handler_verbose(sig, frame):
        """SIGUSR2 - toggle modo verbose."""
        global _verbose
        _verbose = not _verbose
        print(f"\n[Señales] SIGUSR2 - modo verbose: {'ON' if _verbose else 'OFF'}")

    signal.signal(signal.SIGINT, handler_shutdown)
    signal.signal(signal.SIGTERM, handler_shutdown)
    signal.signal(signal.SIGHUP, handler_reload)
    signal.signal(signal.SIGUSR1, handler_dump)
    signal.signal(signal.SIGUSR2, handler_verbose)

    print(f"[Señales] Handlers registrados para PID {os.getpid()}")

def esta_ejecutando():
    return _ejecutando