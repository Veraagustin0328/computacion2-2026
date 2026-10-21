from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from cola import cola, tareas, Tarea, Estado, inicializar_cola

app = FastAPI(title="Plataforma de Tareas Distribuidas")

# modelos de entrada
class TareaInput(BaseModel):
    tipo: str           # "descargar", "hashear", "esperar"
    parametros: dict
    timeout: Optional[int] = 60

@app.on_event("startup")
async def startup():
    inicializar_cola()

@app.post("/tareas", status_code=202)
async def crear_tarea(body: TareaInput):
    tarea = Tarea(body.tipo, body.parametros, body.timeout)
    tareas[tarea.id] = tarea
    await cola.put(tarea)
    return {"id": tarea.id, "estado": tarea.estado}

@app.get("/tareas")
async def listar_tareas(estado: Optional[str] = None):
    resultado = list(tareas.values())
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    return [{"id": t.id, "tipo": t.tipo, "estado": t.estado} for t in resultado]

@app.get("/tareas/{tarea_id}")
async def obtener_tarea(tarea_id: str):
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    t = tareas[tarea_id]
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
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    t = tareas[tarea_id]
    if t.estado in [Estado.completada, Estado.fallida, Estado.cancelada]:
        raise HTTPException(status_code=400, detail=f"No se puede cancelar, estado: {t.estado}")
    t.estado = Estado.cancelada
    if t.asyncio_task:
        t.asyncio_task.cancel()
    return {"id": tarea_id, "estado": t.estado}

@app.get("/estadisticas")
async def estadisticas():
    conteo = {e.value: 0 for e in Estado}
    for t in tareas.values():
        conteo[t.estado] += 1
    return {"totales": conteo, "workers_ocupados": 0}
