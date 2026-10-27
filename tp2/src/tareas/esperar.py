import asyncio

async def ejecutar(parametros: dict) -> dict:
    segundos = parametros.get("segundos", 5)
    await asyncio.sleep(segundos)
    return {"mensaje": f"Esperé {segundos} segundos"}
