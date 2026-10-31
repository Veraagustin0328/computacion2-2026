import asyncio
import time
import aiohttp

BASE = "http://localhost:8000"
ITERACIONES = 20_000_000


async def medir_get(session, duracion):
    # pega GET /tareas cada 0.1s y guarda cuanto tarda cada respuesta
    tiempos = []
    fin = time.perf_counter() + duracion
    while time.perf_counter() < fin:
        inicio = time.perf_counter()
        try:
            async with session.get(f"{BASE}/tareas", timeout=aiohttp.ClientTimeout(total=60)) as r:
                await r.read()
            tiempos.append(time.perf_counter() - inicio)
        except Exception:
            tiempos.append(60.0)
        await asyncio.sleep(0.1)
    return tiempos


async def probar(tipo):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE}/tareas", json={
            "tipo": tipo,
            "parametros": {"texto": "hola", "iteraciones": ITERACIONES},
            "timeout": 120,
        }) as r:
            tarea = await r.json()
        tid = tarea["id"]

        tiempos = await medir_get(session, 8)

        # esperar a que termine para no contaminar la siguiente prueba
        while True:
            async with session.get(f"{BASE}/tareas/{tid}") as r:
                t = await r.json()
            if t["estado"] in ("completada", "fallida", "cancelada"):
                break
            await asyncio.sleep(0.5)

    return tiempos


def resumen(nombre, tiempos):
    print(f"\n{nombre}")
    print(f"  GET /tareas medidos: {len(tiempos)}")
    print(f"  maximo:   {max(tiempos):.3f}s")
    print(f"  promedio: {sum(tiempos)/len(tiempos):.3f}s")


async def main():
    t = await probar("hashear_bloqueante")
    resumen("SIN executor (hashear_bloqueante)", t)
    t = await probar("hashear")
    resumen("CON executor (hashear)", t)


asyncio.run(main())
