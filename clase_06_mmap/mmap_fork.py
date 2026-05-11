import mmap
import os
import struct
import time

mm = mmap.mmap(-1, 256)

pid = os.fork()

if pid == 0:
    print(f"[HIJO {os.getpid()}] Escribiendo datos...")

    struct.pack_into('i', mm, 0, 42)

    mensaje = b"Hola desde el hijo!"
    struct.pack_into('i', mm, 4, len(mensaje))
    mm[8:8+len(mensaje)] = mensaje

    print("[HIJO] Datos escritos, terminando")
    os._exit(0)

else:
    os.wait()
    print(f"[PADRE] Hijo termino, leyendo datos...")

    numero = struct.unpack_from('i', mm, 0)[0]
    print(f"[PADRE] Numero: {numero}")

    largo = struct.unpack_from('i', mm, 4)[0]
    mensaje = bytes(mm[8:8+largo]).decode()
    print(f"[PADRE] Mensaje: {mensaje}")

    mm.close()
