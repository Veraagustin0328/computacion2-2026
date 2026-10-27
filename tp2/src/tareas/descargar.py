
import asyncio
import aiohttp
import time

async def descargar_url(session, url: str) -> dict:
    inicio = time.time()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            contenido = await resp.read()
            duracion = time.time() - inicio
            return {
                "url": url,
                "status": resp.status,
                "tamanio_bytes": len(contenido),
                "duracion_segundos": round(duracion, 3)
            }
    except Exception as e:
        duracion = time.time() - inicio
        return {
            "url": url,
            "status": None,
            "error": str(e),
            "duracion_segundos": round(duracion, 3)
        }

async def ejecutar(parametros: dict) -> dict:
    urls = parametros.get("urls", [])
    if not urls:
        return {"error": "no se mandaron URLs"}

    inicio = time.time()
    async with aiohttp.ClientSession() as session:
        # todas las descargas en paralelo con gather
        resultados = await asyncio.gather(*[descargar_url(session, url) for url in urls])

    duracion_total = time.time() - inicio
    return {
        "resultados": list(resultados),
        "total_urls": len(urls),
        "duracion_total_segundos": round(duracion_total, 3)
    }
