import asyncio
import glob
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import cola as estado
from cola import Tarea, Estado
from workers import iniciar_workers

DIR_ESTADO = os.environ.get("DIR_ESTADO", "/app/datos")
ESPERA_APAGADO = 10  # segundos que esperamos a las tareas en curso

aceptando = True
workers_tasks = []


def volcar_estado():
    os.makedirs(DIR_ESTADO, exist_ok=True)
    nombre = os.path.join(DIR_ESTADO, f"estado_{int(datetime.now().timestamp())}.json")
    datos = {}
    for tid, t in estado.tareas.items():
        datos[tid] = {
            "id": t.id,
            "tipo": t.tipo,
            "estado": t.estado.value,
            "resultado": t.resultado,
            "error": t.error,
            "creada_en": t.creada_en,
            "iniciada_en": t.iniciada_en,
            "terminada_en": t.terminada_en,
        }
    with open(nombre, "w") as f:
        json.dump(datos, f, indent=2)
    print(f"[API] Estado volcado a {nombre} ({len(datos)} tareas)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global aceptando, workers_tasks
    aceptando = True

    # si hay un volcado de una corrida anterior, lo avisamos
    previos = sorted(glob.glob(os.path.join(DIR_ESTADO, "estado_*.json")))
    if previos:
        print(f"[API] Volcado previo encontrado: {previos[-1]} ({len(previos)} en total)")

    estado.cola = asyncio.Queue()
    workers_tasks = await iniciar_workers(n=4)
    print("[API] Cola y workers iniciados")

    yield

    #apagado ordenado
    print("[API] Apagando: no se aceptan tareas nuevas")
    aceptando = False

    en_curso = [t.asyncio_task for t in estado.tareas.values()
                if t.estado == Estado.ejecutando and t.asyncio_task]
    if en_curso:
        print(f"[API] Esperando {len(en_curso)} tarea(s) en curso (max {ESPERA_APAGADO}s)")
        _, pendientes = await asyncio.wait(en_curso, timeout=ESPERA_APAGADO)
        for p in pendientes:
            p.cancel()
        if pendientes:
            await asyncio.gather(*pendientes, return_exceptions=True)

    for w in workers_tasks:
        w.cancel()
    await asyncio.gather(*workers_tasks, return_exceptions=True)

    volcar_estado()


app = FastAPI(title="Plataforma de Tareas Distribuidas", lifespan=lifespan)


class TareaInput(BaseModel):
    tipo: str
    parametros: dict
    timeout: Optional[int] = 60


@app.post("/tareas", status_code=202)
async def crear_tarea(body: TareaInput):
    if not aceptando:
        raise HTTPException(status_code=503, detail="El servicio se esta apagando")
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
    return {"totales": conteo, "workers_ocupados": conteo["ejecutando"]}