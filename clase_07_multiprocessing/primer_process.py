from multiprocessing import Process
import os

def tarea(nombre):
    print(f"[{nombre}] PID={os.getpid()}, PPID={os.getppid()}")
    print(f"[{nombre}] Haciendo trabajo...")

if __name__ == "__main__":
    print(f"[PRINCIPAL] PID={os.getpid()}")

    p = Process(target=tarea, args=("Hijo",))
    p.start()
    p.join()

    print("[PRINCIPAL] Hijo terminó")
