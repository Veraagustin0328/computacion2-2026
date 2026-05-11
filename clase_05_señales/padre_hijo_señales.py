#!/usr/bin/env python3
import os
import signal
import time

pid = os.fork()

if pid == 0:
    contador = 0

    def incrementar(sig, frame):
        global contador
        contador += 1
        print(f"[HIJO] Contador: {contador}")

    def mostrar(sig, frame):
        print(f"[HIJO] Valor actual: {contador}")

    signal.signal(signal.SIGUSR1, incrementar)
    signal.signal(signal.SIGUSR2, mostrar)

    print(f"[HIJO] PID={os.getpid()}, esperando señales...")

    while True:
        signal.pause()

else:
    time.sleep(0.5)

    print("[PADRE] Mandando SIGUSR1 tres veces")
    for _ in range(3):
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.3)

    print("[PADRE] Mandando SIGUSR2 para mostrar")
    os.kill(pid, signal.SIGUSR2)
    time.sleep(0.3)

    print("[PADRE] Dos SIGUSR1 mas")
    for _ in range(2):
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.3)

    print("[PADRE] Mostrando valor final")
    os.kill(pid, signal.SIGUSR2)
    time.sleep(0.3)

    print("[PADRE] Terminando hijo")
    os.kill(pid, signal.SIGTERM)
    os.wait()