import asyncio
import signal
import json
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from workers import iniciar_workers
from cola import tareas, Estado
import api

workers_tasks = []

def volcar_estado():
    timestamp = int(datetime.now().timestamp())
    nombre = f"estado_{timestamp}.json"
    datos = {}
    for tid, t in tareas.items():
        datos[tid] = {
            "id": t.id,
            "tipo": t.tipo,
            "estado": t.estado,
            "resultado": t.resultado,
            "error": t.error,
            "creada_en": t.creada_en,
            "terminada_en": t.terminada_en,
        }
    with open(nombre, "w") as f:
        json.dump(datos, f, indent=2)
    print(f"[Main] Estado volcado a {nombre}")

async def shutdown(loop):
    print("[Main] Apagado ordenado iniciado...")
    for t in workers_tasks:
        t.cancel()
    volcar_estado()
    print("[Main] Listo")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # arrancar workers al iniciar
    global workers_tasks
    workers_tasks = await iniciar_workers(n=4)
    print("[Main] 4 workers iniciados")

    # registrar señales
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    yield

    # al cerrar
    await shutdown(loop)

app = api.app
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
