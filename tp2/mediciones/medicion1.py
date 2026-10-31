import asyncio
import time
import aiohttp

URL = "https://httpbin.org/delay/1"  # tarda 1 seg en responder
N = 20


async def descargar(session, url):
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        await resp.read()
        return resp.status


async def secuencial():
    inicio = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        for _ in range(N):
            await descargar(session, URL)
    return time.perf_counter() - inicio


async def concurrente():
    inicio = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[descargar(session, URL) for _ in range(N)])
    return time.perf_counter() - inicio


async def main():
    t_seq = await secuencial()
    print(f"Secuencial ({N} descargas):  {t_seq:.2f}s")
    t_con = await concurrente()
    print(f"Concurrente ({N} descargas): {t_con:.2f}s")
    print(f"Speedup: {t_seq / t_con:.1f}x")


asyncio.run(main())
