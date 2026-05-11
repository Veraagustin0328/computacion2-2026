import mmap
import struct
import os
from multiprocessing import Process

ARCHIVO = "/tmp/mmap_mp.bin"
TAMAÑO = 256

with open(ARCHIVO, "wb") as f:
    f.write(b'\x00' * TAMAÑO)

def escribir_en_mmap(archivo, offset, mensaje):
    with open(archivo, "r+b") as f:
        mm = mmap.mmap(f.fileno(), TAMAÑO)
        encoded = mensaje.encode()
        struct.pack_into('i', mm, offset, len(encoded))
        mm[offset+4:offset+4+len(encoded)] = encoded
        mm.close()

procesos = []
mensajes = [
    "Hola desde proceso 0",
    "Saludos del proceso 1",
    "Proceso 2 presente",
    "Proceso 3 reportando",
]

for i, msg in enumerate(mensajes):
    p = Process(target=escribir_en_mmap, args=(ARCHIVO, i * 64, msg))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)
    print("=== Mensajes de los procesos ===")
    for i in range(4):
        offset = i * 64
        largo = struct.unpack_from('i', mm, offset)[0]
        if largo > 0:
            msg = bytes(mm[offset+4:offset+4+largo]).decode()
            print(f"  Proceso {i}: {msg}")
    mm.close()

os.unlink(ARCHIVO)
