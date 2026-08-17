# descargador.py - descargador paralelo con threads (OBLIGATORIO)
# Agustin Vera - Computacion II 2026

import threading
import urllib.request
import time
import os
from queue import Queue

lock_print = threading.Lock()
resultados = {}

def descargar(url, destino, semaforo, resultados):
    with semaforo:
        inicio = time.time()
        try:
            with lock_print:
                print(f"[Descargando] {url}")
            urllib.request.urlretrieve(url, destino)
            duracion = time.time() - inicio
            tamanio = os.path.getsize(destino)
            with lock_print:
                print(f"[OK] {url} -> {destino} ({tamanio} bytes, {duracion:.2f}s)")
            resultados[url] = {"estado": "ok", "tamanio": tamanio, "duracion": duracion}
        except Exception as e:
            duracion = time.time() - inicio
            with lock_print:
                print(f"[ERROR] {url}: {e}")
            resultados[url] = {"estado": "error", "error": str(e), "duracion": duracion}

if __name__ == "__main__":
    urls = [
        ("https://www.google.com", "/tmp/google.html"),
        ("https://www.python.org", "/tmp/python.html"),
        ("https://httpbin.org/get", "/tmp/httpbin.json"),
        ("https://jsonplaceholder.typicode.com/posts/1", "/tmp/post1.json"),
        ("https://jsonplaceholder.typicode.com/posts/2", "/tmp/post2.json"),
        ("https://jsonplaceholder.typicode.com/users/1", "/tmp/user1.json"),
    ]

    MAX_CONCURRENTES = 3
    semaforo = threading.Semaphore(MAX_CONCURRENTES)

    print(f"Descargando {len(urls)} archivos con max {MAX_CONCURRENTES} concurrentes\n")
    inicio = time.time()

    threads = []
    for url, destino in urls:
        t = threading.Thread(target=descargar, args=(url, destino, semaforo, resultados))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    duracion_total = time.time() - inicio

    print(f"\n=== Resumen ===")
    exitosos = sum(1 for r in resultados.values() if r["estado"] == "ok")
    fallidos = sum(1 for r in resultados.values() if r["estado"] == "error")
    print(f"Exitosos: {exitosos} | Fallidos: {fallidos}")
    print(f"Tiempo total: {duracion_total:.2f}s")
