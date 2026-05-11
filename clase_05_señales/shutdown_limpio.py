#!/usr/bin/env python3
import signal
import sys
import time
import os

class Aplicacion:
    def __init__(self):
        self.ejecutando = True
        self.recursos = []

        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, sig, frame):
        nombre_señal = signal.Signals(sig).name
        print(f"\nRecibi {nombre_señal}, cerrando...")
        self.ejecutando = False

    def adquirir_recurso(self, nombre):
        print(f"Adquiriendo: {nombre}")
        self.recursos.append(nombre)

    def liberar_recursos(self):
        for recurso in reversed(self.recursos):
            print(f"Liberando: {recurso}")
            time.sleep(0.3)
        self.recursos.clear()

    def run(self):
        print(f"PID: {os.getpid()}")
        print("Manda kill <pid> para terminar limpiamente")

        self.adquirir_recurso("base_de_datos")
        self.adquirir_recurso("archivo_log")
        self.adquirir_recurso("conexion_red")

        while self.ejecutando:
            print("Trabajando...")
            time.sleep(1)

        self.liberar_recursos()
        print("Aplicacion terminada")

if __name__ == "__main__":
    app = Aplicacion()
    app.run()