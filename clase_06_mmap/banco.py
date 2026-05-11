from multiprocessing import Process, Array
import random
import time

NUM_CUENTAS = 5
SALDO_INICIAL = 1000
NUM_PROCESOS = 3
TRANSFERENCIAS_POR_PROCESO = 100

def mostrar_saldos(cuentas, etiqueta):
    saldos = [cuentas[i] for i in range(NUM_CUENTAS)]
    total = sum(saldos)
    print(f"[{etiqueta}] Saldos: {saldos} | Total: {total}")

def cajero(cuentas, cajero_id, num_transferencias):
    for _ in range(num_transferencias):
        origen = random.randint(0, NUM_CUENTAS - 1)
        destino = random.randint(0, NUM_CUENTAS - 1)
        while destino == origen:
            destino = random.randint(0, NUM_CUENTAS - 1)

        monto = random.randint(1, 50)

        if cuentas[origen] >= monto:
            cuentas[origen] -= monto
            cuentas[destino] += monto

    print(f"[Cajero {cajero_id}] Completo {num_transferencias} transferencias")

cuentas = Array('i', [SALDO_INICIAL] * NUM_CUENTAS)

print(f"=== Banco con {NUM_CUENTAS} cuentas ===")
print(f"=== Saldo total esperado: {NUM_CUENTAS * SALDO_INICIAL} ===\n")

mostrar_saldos(cuentas, "INICIO")

procesos = []
for i in range(NUM_PROCESOS):
    p = Process(target=cajero, args=(cuentas, i, TRANSFERENCIAS_POR_PROCESO))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

mostrar_saldos(cuentas, "FINAL")

total_final = sum(cuentas[i] for i in range(NUM_CUENTAS))
total_esperado = NUM_CUENTAS * SALDO_INICIAL

if total_final != total_esperado:
    print(f"\nERROR! Se perdieron ${total_esperado - total_final}")
    print("Esto es una race condition - se necesita sincronizacion")
else:
    print(f"\nTodo correcto (pero fue suerte - ejecutalo varias veces)")
