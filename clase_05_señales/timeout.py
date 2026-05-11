#!/usr/bin/env python3
import signal
import time

class Timeout(Exception):
    pass

def timeout_handler(sig, frame):
    raise Timeout("La operacion tardo demasiado")

def con_timeout(segundos):
    def decorador(func):
        def wrapper(*args, **kwargs):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(segundos)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorador

@con_timeout(3)
def operacion_lenta():
    print("Iniciando operacion lenta...")
    time.sleep(5)
    return "Completado"

@con_timeout(3)
def operacion_rapida():
    print("Iniciando operacion rapida...")
    time.sleep(1)
    return "Completado"

print("=== Operacion rapida ===")
try:
    resultado = operacion_rapida()
    print(f"Resultado: {resultado}")
except Timeout as e:
    print(f"Timeout: {e}")

print("\n=== Operacion lenta ===")
try:
    resultado = operacion_lenta()
    print(f"Resultado: {resultado}")
except Timeout as e:
    print(f"Timeout: {e}")