# test rapido del display
import sys
sys.path.insert(0, '.')
from multiprocessing import Manager, Value
import time

with Manager() as manager:
    snapshot = manager.dict()
    snapshot["resumen"] = {
        "datos": {
            1: {"pid": 1, "nombre": "systemd", "estado": "S", "cpu_pct": 0.0, "rss_kb": 12000, "threads": 1, "uid": "0", "cmdline": "/sbin/init", "ppid": 0},
            2: {"pid": 2, "nombre": "bash", "estado": "S", "cpu_pct": 0.1, "rss_kb": 5000, "threads": 1, "uid": "1000", "cmdline": "bash", "ppid": 1},
        },
        "timestamp": time.time()
    }
    snapshot["sistema"] = {"datos": {}, "timestamp": 0}
    snapshot["memoria"] = {"datos": {}, "timestamp": 0}
    snapshot["fds"] = {"datos": {}, "timestamp": 0}
    snapshot["threads"] = {"datos": {}, "timestamp": 0}
    snapshot["senales"] = {"datos": {}, "timestamp": 0}
    snapshot["scheduling"] = {"datos": {}, "timestamp": 0}

    intervalos = {
        "resumen": Value('d', 2.0),
        "memoria": Value('d', 3.0),
        "fds": Value('d', 5.0),
        "threads": Value('d', 2.0),
        "senales": Value('d', 10.0),
        "scheduling": Value('d', 10.0),
        "sistema": Value('d', 2.0),
    }

    from display import iniciar_display
    iniciar_display(snapshot, intervalos)
