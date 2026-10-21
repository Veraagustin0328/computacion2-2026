import asyncio
from datetime import datetime
from cola import cola, tareas, Estado

async def ejecutar_tarea(tarea):
    # por ahora simula ejecucion, la logica real va en semana 2
    tarea.estado = Estado.ejecutando
    tarea.iniciada_en = datetime.now().isoformat()

    await asyncio.sleep(2)  # simulacion

    tarea.estado = Estado.completada
    tarea.resultado = {"mensaje": f"tarea {tarea.tipo} completada (simulado)"}
    tarea.terminada_en = datetime.now().isoformat()

async def worker(worker_id):
    print(f"[Worker {worker_id}] Iniciando")
    while True:
        tarea = await cola.get()

        if tarea.estado == Estado.cancelada:
            cola.task_done()
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
            tarea.error = "timeout"
            tarea.terminada_en = datetime.now().isoformat()
        except Exception as e:
            tarea.estado = Estado.fallida
            tarea.error = str(e)
            tarea.terminada_en = datetime.now().isoformat()

        cola.task_done()

async def iniciar_workers(n=4):
    workers = [asyncio.create_task(worker(i)) for i in range(n)]
    return workers
