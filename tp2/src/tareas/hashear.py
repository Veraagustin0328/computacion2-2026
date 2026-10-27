

import asyncio
import hashlib
import time

def calcular_hash(texto: str, iteraciones: int) -> dict:
    # esto bloquea - por eso va en executor
    inicio = time.time()
    resultado = texto.encode()
    for _ in range(iteraciones):
        resultado = hashlib.sha256(resultado).digest()
    duracion = time.time() - inicio
    return {
        "hash": resultado.hex(),
        "iteraciones": iteraciones,
        "duracion_segundos": round(duracion, 3)
    }

async def ejecutar(parametros: dict) -> dict:
    texto = parametros.get("texto", "hola mundo")
    iteraciones = parametros.get("iteraciones", 100000)

    loop = asyncio.get_event_loop()
    resultado = await loop.run_in_executor(None, calcular_hash, texto, iteraciones)
    return resultado
