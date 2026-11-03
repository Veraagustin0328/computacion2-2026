# TP2 - Plataforma de tareas distribuidas

Computación II - 2026 - Agustín Vera (legajo 61221)

Es un servicio al que le mandás tareas por HTTP. Responde enseguida con un id, las ejecuta de fondo con un pool de workers y después podés consultar cómo le fue. Está hecho con FastAPI y asyncio. La cola la armé con `asyncio.Queue`, sin Celery ni nada parecido.

## Cómo se usa

```bash
git clone https://github.com/Veraagustin0328/computacion2-2026.git
cd computacion2-2026/tp2
docker compose up --build
```

La API queda en `http://localhost:8001`. En el compose publiqué el 8001 porque en mi compu el 8000 ya lo usaba otra cosa. Si a vos te molesta, cambialo en `docker-compose.yml`.

Ejemplos:

```bash
# esperar 3 segundos
curl -X POST http://localhost:8001/tareas -H "Content-Type: application/json" \
  -d '{"tipo": "esperar", "parametros": {"segundos": 3}}'

# hash iterado (CPU)
curl -X POST http://localhost:8001/tareas -H "Content-Type: application/json" \
  -d '{"tipo": "hashear", "parametros": {"texto": "hola", "iteraciones": 1000000}}'

# descargar URLs
curl -X POST http://localhost:8001/tareas -H "Content-Type: application/json" \
  -d '{"tipo": "descargar", "parametros": {"urls": ["https://httpbin.org/get"]}}'

# con timeout propio (segundos)
curl -X POST http://localhost:8001/tareas -H "Content-Type: application/json" \
  -d '{"tipo": "esperar", "parametros": {"segundos": 30}, "timeout": 3}'

# ver una tarea, listar, cancelar, estadísticas
curl http://localhost:8001/tareas/ID
curl http://localhost:8001/tareas
curl "http://localhost:8001/tareas?estado_filtro=completada"
curl -X DELETE http://localhost:8001/tareas/ID
curl http://localhost:8001/estadisticas
```

Estados: `pendiente`, `ejecutando`, `completada`, `fallida`, `cancelada`.

## Arquitectura

```
Cliente HTTP
     |
     v
┌──────────────────┐        ┌──────────────────┐
│   API (FastAPI)  │───────>│  asyncio.Queue   │
│  POST /tareas    │ put()  └────────┬─────────┘
│  GET  /tareas    │                 │ get()
│  GET  /tareas/id │                 v
│  DEL  /tareas/id │        ┌──────────────────┐
└──────────────────┘        │  4 workers       │
        ^                   │  (corrutinas)    │
        │  estado/resultado │  hashear ->      │
        └───────────────────┤  run_in_executor │
        (dict en memoria)   └──────────────────┘
```

Lo que pasa con una tarea:

1. El `POST` crea la `Tarea`, la guarda en un diccionario y la mete en la cola.
2. Responde con el id sin esperar nada.
3. Un worker libre la saca de la cola y la corre con un timeout.
4. Guarda el resultado en el mismo diccionario.
5. Yo consulto con el id cuando quiero.

Archivos:

- `src/api.py`: endpoints, arranque y apagado
- `src/cola.py`: la clase `Tarea`, los estados, la cola y el diccionario
- `src/workers.py`: el pool
- `src/tareas/`: `esperar.py`, `hashear.py`, `descargar.py`
- `src/tareas/hashear_bloqueante.py`: la versión mala, solo para la medición 2
- `mediciones/`: los tres scripts

## Decisiones de diseño

**¿Por qué `asyncio.Queue` y no `queue.Queue`?**
Con `queue.Queue`, un `get()` sobre una cola vacía bloquea el hilo. Si lo hace un worker dentro del event loop, se congela toda la API. Con `asyncio.Queue` el `get()` es un `await`: el worker espera y el loop sigue atendiendo pedidos.

**¿Cómo evito que `hashear` congele la API?**
Calculo el hash en otro thread con `loop.run_in_executor`. El loop solo hace `await` del resultado y mientras tanto atiende lo demás. La medición 2 muestra la diferencia.

**¿Cómo cancelo?**
Cada tarea en ejecución es una `asyncio.Task` y me guardo la referencia. El `DELETE` marca la tarea como `cancelada` y llama a `task.cancel()`, que tira un `CancelledError` en el próximo `await` de la tarea. Eso la corta y cierra lo que estaba abierto con `async with`, como la sesión de aiohttp. Si la tarea todavía estaba en la cola, el worker la descarta cuando la saca.

**¿Y si un worker tira una excepción?**
Cada tarea corre dentro de un `try/except`. Si algo explota, la tarea queda `fallida` con el mensaje de error y el worker sigue con la próxima. Una tarea rota no mata el pool.

**¿Por qué `aiohttp` y no `requests`?**
`requests` es bloqueante: una descarga frenaría el loop entero. Con `aiohttp` hago `await` y puedo largar todas las descargas juntas con `asyncio.gather`.

**Apagado ordenado.**
Con SIGTERM o SIGINT, uvicorn corre lo que está después del `yield` del `lifespan`. Ahí:

- dejo de aceptar tareas (el `POST` devuelve 503)
- espero hasta 10 segundos a las que están corriendo
- cancelo las que sigan
- guardo todo en `datos/estado_<timestamp>.json`

Cuando arranca, si encuentra un volcado anterior lo avisa por log.

## Mediciones

Las corrí adentro del contenedor, con los scripts de `mediciones/`.

**1. Concurrencia I/O.** 20 descargas de `https://httpbin.org/delay/1`.

| | Tiempo |
|---|---|
| Secuencial | 26,16 s |
| Concurrente | 1,90 s |
| Speedup | 13,8x |

Las 20 concurrentes tardaron casi lo mismo que la más lenta. No dio 20x porque cada pedido tarda un poco más que 1 s (red, TLS).

**2. Event loop bloqueado.** Un hash de 20 millones de iteraciones y un `GET /tareas` cada 0,1 s durante 8 s.

| | GET medidos | Máximo | Promedio |
|---|---|---|---|
| Sin executor | 1 | 19,444 s | 19,444 s |
| Con executor | 68 | 0,021 s | 0,015 s |

Sin executor el hash corre en el mismo hilo que atiende HTTP y no tiene ningún `await`. El loop no puede hacer nada hasta que termina, y el único `GET` que pude medir tardó todo lo que duró el hash. Con executor, la API respondió en milisegundos. Esto depende de mi CPU y de las 20 millones de iteraciones.

**3. Techo del pool.** Tareas `esperar` de 1 s, 4 workers, de 4 a 1024 tareas.

| Tareas | Total | Ideal (N/4) | Tareas/s |
|---|---|---|---|
| 4 | 1,07 s | 1,0 s | 3,8 |
| 64 | 16,11 s | 16,0 s | 4,0 |
| 256 | 64,39 s | 64,0 s | 4,0 |
| 1024 | 257,37 s | 256,0 s | 4,0 |

El tiempo crece parejo y siempre quedó a menos del 1% del ideal. El techo es 4 tareas por segundo: 4 workers haciendo 1 tarea por segundo cada uno. Ese límite lo pone el tamaño del pool, no una saturación del sistema. Encolar las 1024 tareas tardó 1,64 s.

Con 4 workers no logré hacer que se degrade, así que no encontré el punto de quiebre real. No probé subir la cantidad de workers.

## Conceptos del curso

- **Productor-consumidor (clase 11).** El `POST` produce y los workers consumen de la cola. Es el patrón de la clase 11 pero con corrutinas. No usé `Lock` porque el event loop corre en un solo hilo y no se interrumpe entre `await`s, así que las operaciones sobre el diccionario y la cola no se pisan.
- **Event loop y multiplexing (clases 17 y 18).** Un solo hilo atiende muchas cosas porque cada corrutina suelta el control en el `await`. Por eso `time.sleep()` dentro de una corrutina es un bug: frena el hilo entero. `asyncio.sleep()` en cambio cede el control.
- **GIL y threads (clase 10).** El hash es CPU-bound, así que lo mando a un thread para sacarlo del loop.
- **FastAPI y asyncio en red (clases 19 y 20).** Los endpoints son `async` y las descargas usan `aiohttp`.
- **Señales (clase 6).** El apagado ordenado se dispara con SIGTERM y SIGINT.

## Limitaciones

- El estado vive en memoria. Si el proceso se cae sin apagado ordenado, se pierde todo. El JSON solo se guarda al apagar.
- El diccionario de tareas nunca se limpia, así que la memoria crece con cada tarea. Si me mandan 10.000 de golpe, lo primero que se rompería es la memoria. Además la cola no tiene límite.
- `hashear` usa el executor por defecto (threads), que comparten el GIL. No aprovecha varios núcleos. Para eso haría falta un `ProcessPoolExecutor`.
- Cancelar una tarea que está en el executor no corta el cálculo: el thread termina el hash aunque la tarea figure como `cancelada`.
- Probé un timeout de 3 s y la tarea quedó `fallida` a los 1,4 s según los timestamps, no a los 3. El estado final es el correcto, pero no entendí por qué se cortó antes.
- Los workers están fijos en 4, no es configurable.
- No hay autenticación ni límite de tareas por cliente.
- `hashear_bloqueante` quedó registrado como tipo de tarea solo para poder hacer la medición 2.

## Lo que aprendí

Lo que más me quedó es la diferencia entre I/O y CPU. Las 20 descargas pasaron de 26 s a 1,9 s con asyncio, pero el hash dejó la API muerta casi 20 segundos hasta que lo mandé al executor. Verlo con números me lo hizo entender mejor que leerlo.

Me trabé más de lo que pensaba con cosas de arranque. Los workers arrancaban antes de que existiera la cola y fallaban con un `NoneType`, y tuve el `lifespan` duplicado entre `main.py` y `api.py`. Me costó ver que era un tema de orden de inicialización y no de la lógica.

También me sirvió probar la cancelación y el apagado de verdad, y no solo escribirlos. Ahí vi que el estado quedaba bien y que el volcado a JSON se generaba.