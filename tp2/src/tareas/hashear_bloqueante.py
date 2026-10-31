import hashlib


async def ejecutar(parametros: dict) -> dict:
    texto = parametros.get("texto", "hola mundo")
    iteraciones = parametros.get("iteraciones", 100000)
    resultado = texto.encode()
    for _ in range(iteraciones):
        resultado = hashlib.sha256(resultado).digest()
    return {"hash": resultado.hex(), "iteraciones": iteraciones}
