from multiprocessing import Process, Array
import time

def calcular_rango(resultado, inicio, fin):
    for i in range(inicio, fin):
        resultado[i] = i * i

TAMAÑO = 1000
resultado = Array('i', TAMAÑO)

NUM_PROCESOS = 4
chunk = TAMAÑO // NUM_PROCESOS

inicio = time.time()

procesos = []
for i in range(NUM_PROCESOS):
    ini = i * chunk
    fin = (i + 1) * chunk if i < NUM_PROCESOS - 1 else TAMAÑO
    p = Process(target=calcular_rango, args=(resultado, ini, fin))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

duracion = time.time() - inicio

print(f"Calculo completado en {duracion:.4f}s")
print(f"resultado[0] = {resultado[0]}")
print(f"resultado[10] = {resultado[10]}")
print(f"resultado[99] = {resultado[99]}")
print(f"resultado[999] = {resultado[999]}")

errores = sum(1 for i in range(TAMAÑO) if resultado[i] != i * i)
print(f"Errores: {errores}")
