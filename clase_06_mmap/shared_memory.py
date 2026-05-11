from multiprocessing import Process, shared_memory
import struct
import time

def productor(shm_name, num_valores):
    shm = shared_memory.SharedMemory(name=shm_name)

    for i in range(num_valores):
        struct.pack_into('i', shm.buf, i * 4, i * i)

    shm.buf[-1] = 1
    print(f"[PRODUCTOR] Escribi {num_valores} valores")
    shm.close()

def consumidor(shm_name, num_valores):
    shm = shared_memory.SharedMemory(name=shm_name)

    while shm.buf[-1] != 1:
        time.sleep(0.01)

    valores = []
    for i in range(num_valores):
        val = struct.unpack_from('i', shm.buf, i * 4)[0]
        valores.append(val)

    print(f"[CONSUMIDOR] Lei: {valores}")
    shm.close()

NUM = 10
shm = shared_memory.SharedMemory(create=True, size=NUM * 4 + 1)

p_prod = Process(target=productor, args=(shm.name, NUM))
p_cons = Process(target=consumidor, args=(shm.name, NUM))

p_cons.start()
p_prod.start()

p_prod.join()
p_cons.join()

shm.close()
shm.unlink()
