from multiprocessing import Process, Pipe

def hijo(conn):
    for i in range(5):
        msg = conn.recv()
        print(f"[HIJO] Recibi: {msg}")
        respuesta = f"pong_{i}"
        conn.send(respuesta)
        print(f"[HIJO] Mande: {respuesta}")
    conn.close()

if __name__ == "__main__":
    padre_conn, hijo_conn = Pipe()

    p = Process(target=hijo, args=(hijo_conn,))
    p.start()

    for i in range(5):
        msg = f"ping_{i}"
        padre_conn.send(msg)
        print(f"[PADRE] Mande: {msg}")
        respuesta = padre_conn.recv()
        print(f"[PADRE] Recibi: {respuesta}")

    padre_conn.close()
    p.join()
    print("Ping-pong terminado")
