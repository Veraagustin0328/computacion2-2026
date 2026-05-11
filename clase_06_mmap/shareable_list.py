from multiprocessing import Process, shared_memory

def actualizar_datos(nombre_shm):
    sl = shared_memory.ShareableList(name=nombre_shm)

    sl[0] = 42
    sl[1] = 3.14159
    sl[2] = "actualizado"
    sl[3] = False

    print(f"[WORKER] Lista actualizada: {list(sl)}")
    sl.shm.close()

sl = shared_memory.ShareableList(
    [0, 0.0, "          ", True],
    name="mi_lista_comp"
)

print(f"Antes:   {list(sl)}")

p = Process(target=actualizar_datos, args=(sl.shm.name,))
p.start()
p.join()

print(f"Despues: {list(sl)}")

sl.shm.close()
sl.shm.unlink()
