# thread_clase.py - thread usando herencia de clase
# Agustin Vera - Computacion II 2026

import threading
import time

class MiThread(threading.Thread):
    def __init__(self, nombre, repeticiones):
        super().__init__()
        self.nombre = nombre
        self.repeticiones = repeticiones
        self.resultado = None

    def run(self):
        print(f"[{self.nombre}] Iniciando")
        total = 0
        for i in range(self.repeticiones):
            total += i
            time.sleep(0.01)
        self.resultado = total
        print(f"[{self.nombre}] Termino, resultado={self.resultado}")

if __name__ == "__main__":
    threads = [
        MiThread("Worker-1", 100),
        MiThread("Worker-2", 200),
        MiThread("Worker-3", 50),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()
        print(f"Resultado de {t.nombre}: {t.resultado}")
