import mmap

with open("/tmp/mmap_test.txt", "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    print(f"Contenido: {mm[:40]}")
    print(f"Tamaño: {mm.size()} bytes")

    try:
        mm[0:4] = b"TEST"
    except TypeError as e:
        print(f"Error al escribir: {e}")

    mm.close()
