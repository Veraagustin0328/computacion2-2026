import time
from contextlib import contextmanager


class Timer:
    """Context manager que mide el tiempo de ejecución de un bloque de código."""

    def __init__(self, nombre: str = None):
        self.nombre = nombre
        self.elapsed = 0.0
        self._inicio = None

    def __enter__(self):
        self._inicio = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed = time.time() - self._inicio
        if self.nombre:
            print(f"[Timer] {self.nombre}: {self.elapsed:.3f}s")
        return False

    @property
    def elapsed(self):
        if self._inicio is not None:
            return time.time() - self._inicio
        return self._elapsed

    @elapsed.setter
    def elapsed(self, value):
        self._elapsed = value


@contextmanager
def timer(nombre: str = None):
    """Version con @contextmanager del Timer."""
    inicio = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - inicio
        if nombre:
            print(f"[Timer] {nombre}: {elapsed:.3f}s")


if __name__ == "__main__":
    # Ejemplo 1: con nombre
    with Timer("Procesamiento de datos"):
        datos = [x**2 for x in range(1000000)]

    # Ejemplo 2: sin nombre, accediendo a elapsed
    with Timer() as t:
        time.sleep(0.5)
    print(f"El bloque tardó {t.elapsed:.3f} segundos")

    # Ejemplo 3: acceso durante el bloque
    with Timer() as t:
        time.sleep(0.2)
        print(f"Después del paso 1: {t.elapsed:.3f}s")
        time.sleep(0.2)
        print(f"Después del paso 2: {t.elapsed:.3f}s")
