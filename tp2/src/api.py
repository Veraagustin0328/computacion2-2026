

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import asyncio
import cola as estado
from cola import Tarea, Estado
from workers import iniciar_workers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # inicializar cola y workers al arrancar
    estado.cola = asyncio.Queue()
    await iniciar_workers(n=4)
    print("[API] Cola y workers iniciados")
    yield
    print("[API] Apagando...")

app = FastAPI(title="Plataforma de Tareas Distribuidas", lifespan=lifespan)

class TareaInput(BaseModel):
    tipo: str
    parametros: dict
    timeout: Optional[int] = 60

@app.post("/tareas", status_code=202)
async def crear_tarea(body: TareaInput):
    tarea = Tarea(body.tipo, body.parametros, body.timeout)
    estado.tareas[tarea.id] = tarea
    await estado.cola.put(tarea)
    return {"id": tarea.id, "estado": tarea.estado}

@app.get("/tareas")
async def listar_tareas(estado_filtro: Optional[str] = None):
    resultado = list(estado.tareas.values())
    if estado_filtro:
        resultado = [t for t in resultado if t.estado == estado_filtro]
    return [{"id": t.id, "tipo": t.tipo, "estado": t.estado} for t in resultado]

@app.get("/tareas/{tarea_id}")
async def obtener_tarea(tarea_id: str):
    if tarea_id not in estado.tareas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    t = estado.tareas[tarea_id]
    return {
        "id": t.id,
        "tipo": t.tipo,
        "estado": t.estado,
        "resultado": t.resultado,
        "error": t.error,
        "creada_en": t.creada_en,
        "iniciada_en": t.iniciada_en,
        "terminada_en": t.terminada_en,
    }

@app.delete("/tareas/{tarea_id}")
async def cancelar_tarea(tarea_id: str):
    if tarea_id not in estado.tareas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    t = estado.tareas[tarea_id]
    if t.estado in [Estado.completada, Estado.fallida, Estado.cancelada]:
        raise HTTPException(status_code=400, detail=f"No se puede cancelar, estado: {t.estado}")
    t.estado = Estado.cancelada
    if t.asyncio_task:
        t.asyncio_task.cancel()
    return {"id": tarea_id, "estado": t.estado}

@app.get("/estadisticas")
async def estadisticas():
    conteo = {e.value: 0 for e in Estado}
    for t in estado.tareas.values():
        conteo[t.estado] += 1
    workers_ocupados = sum(1 for t in estado.tareas.values() if t.estado == Estado.ejecutando)
    return {"totales": conteo, "workers_ocupados": workers_ocupados}
