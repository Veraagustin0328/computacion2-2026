import time
import random
from functools import wraps


def retry(max_attempts: int = 3, delay: float = 1, exceptions: tuple = (Exception,)):
    """
    Decorador que reintenta una función si falla.
    
    Args:
        max_attempts: número máximo de intentos (default: 3)
        delay: segundos entre intentos (default: 1)
        exceptions: tupla de excepciones a capturar (default: Exception)
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_error = None
            for intento in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    ultimo_error = e
                    if intento < max_attempts:
                        print(f"Intento {intento}/{max_attempts} falló: {e}. Esperando {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"Intento {intento}/{max_attempts} falló: {e}.")
            raise ultimo_error
        return wrapper
    return decorador


if __name__ == "__main__":
    @retry(max_attempts=3, delay=1)
    def conectar_servidor():
        if random.random() < 0.7:
            raise ConnectionError("Servidor no disponible")
        return "Conectado exitosamente"

    try:
        resultado = conectar_servidor()
        print(resultado)
    except ConnectionError:
        print("Falló después de 3 intentos")
