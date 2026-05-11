import mmap
import struct
import os

ARCHIVO = "/tmp/numeros.bin"
NUM_ELEMENTOS = 10
TAMAÑO = NUM_ELEMENTOS * 4

with open(ARCHIVO, "wb") as f:
    f.write(b'\x00' * TAMAÑO)

with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)

    print("Escribiendo numeros...")
    for i in range(NUM_ELEMENTOS):
        valor = (i + 1) * 100
        struct.pack_into('i', mm, i * 4, valor)
        print(f"  Posicion {i}: {valor}")

    print("\nLeyendo numeros...")
    for i in range(NUM_ELEMENTOS):
        valor = struct.unpack_from('i', mm, i * 4)[0]
        print(f"  Posicion {i}: {valor}")

    struct.pack_into('i', mm, 3 * 4, 9999)
    print(f"\nPosicion 3 modificada a: {struct.unpack_from('i', mm, 3 * 4)[0]}")

    mm.close()

os.unlink(ARCHIVO)
