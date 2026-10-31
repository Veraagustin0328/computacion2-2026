import asyncio
import time
import aiohttp

BASE = "http://localhost:8000"
CANTIDADES = [4, 8, 16, 32, 64, 128, 256, 512, 1024]


async def correr(session, n):
    inicio = time.perf_counter()
    ids = []
    for _ in range(n):
        async with session.post(f"{BASE}/tareas", json={
            "tipo": "esperar", "parametros": {"segundos": 1}, "timeout": 300,
        }) as r:
            ids.append((await r.json())["id"])
    t_encolado = time.perf_counter() - inicio

    while True:
        async with session.get(f"{BASE}/tareas?estado_filtro=completada") as r:
            hechas = await r.json()
        # cuento solo las de esta tanda
        propias = {t["id"] for t in hechas} & set(ids)
        if len(propias) == n:
            break
        await asyncio.sleep(0.2)

    total = time.perf_counter() - inicio
    return t_encolado, total


async def main():
    print(f"{'tareas':>7} {'encolar':>9} {'total':>9} {'ideal':>8} {'tareas/s':>9}")
    async with aiohttp.ClientSession() as session:
        for n in CANTIDADES:
            t_enc, total = await correr(session, n)
            ideal = n / 4
            print(f"{n:>7} {t_enc:>8.2f}s {total:>8.2f}s {ideal:>7.1f}s {n/total:>9.1f}")


asyncio.run(main())
