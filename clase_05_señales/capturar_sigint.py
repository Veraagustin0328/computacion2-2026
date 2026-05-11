#!/usr/bin/env python3
import signal
import time

contador_ctrl_c = 0

def manejador_sigint(sig, frame):
    global contador_ctrl_c
    contador_ctrl_c += 1
    print(f"\nCtrl+C presionado {contador_ctrl_c} vez/veces")

    if contador_ctrl_c >= 3:
        print("Saliendo...")
        raise SystemExit(0)
    else:
        print(f"Faltan {3 - contador_ctrl_c} veces mas para salir")

signal.signal(signal.SIGINT, manejador_sigint)

print("Programa corriendo, apreta Ctrl+C tres veces para salir")

while True:
    print(".", end="", flush=True)
    time.sleep(0.5)
    
