import asyncio
from datetime import datetime
from cola import Estado
import cola as estado
from tareas import esperar, hashear, descargar

TAREAS = {
    "esperar":   esperar.ejecutar,
    "hashear":   hashear.ejecutar,
    "descargar": descargar.ejecutar,
}

async def ejecutar_tarea(tarea):
    tarea.estado = Estado.ejecutando
    tarea.iniciada_en = datetime.now().isoformat()

    funcion = TAREAS.get(tarea.tipo)
    if not funcion:
        raise ValueError(f"tipo de tarea desconocido: {tarea.tipo}")

    resultado = await funcion(tarea.parametros)
    tarea.resultado = resultado
    tarea.estado = Estado.completada
    tarea.terminada_en = datetime.now().isoformat()

async def worker(worker_id):
    print(f"[Worker {worker_id}] Iniciando")
    while True:
        # espera hasta que la cola este inicializada
        while estado.cola is None:
            await asyncio.sleep(0.1)

        tarea = await estado.cola.get()

        if tarea.estado == Estado.cancelada:
            estado.cola.task_done()
            continue

        print(f"[Worker {worker_id}] Ejecutando tarea {tarea.id} ({tarea.tipo})")
        try:
            task = asyncio.create_task(ejecutar_tarea(tarea))
            tarea.asyncio_task = task
            await asyncio.wait_for(task, timeout=tarea.timeout)
        except asyncio.CancelledError:
            tarea.estado = Estado.cancelada
            tarea.terminada_en = datetime.now().isoformat()
        except asyncio.TimeoutError:
            tarea.estado = Estado.fallida
            tarea.error = f"timeout despues de {tarea.timeout}s"
            tarea.terminada_en = datetime.now().isoformat()
        except Exception as e:
            tarea.estado = Estado.fallida
            tarea.error = str(e)
            tarea.terminada_en = datetime.now().isoformat()

        estado.cola.task_done()

async def iniciar_workers(n=4):
    workers = [asyncio.create_task(worker(i)) for i in range(n)]
    return workers