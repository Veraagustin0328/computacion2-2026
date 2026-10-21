
import asyncio
import uuid
from datetime import datetime
from enum import Enum

class Estado(str, Enum):
    pendiente  = "pendiente"
    ejecutando = "ejecutando"
    completada = "completada"
    fallida    = "fallida"
    cancelada  = "cancelada"

class Tarea:
    def __init__(self, tipo, parametros, timeout=60):
        self.id         = str(uuid.uuid4())
        self.tipo       = tipo
        self.parametros = parametros
        self.timeout    = timeout
        self.estado     = Estado.pendiente
        self.resultado  = None
        self.error      = None
        self.creada_en  = datetime.now().isoformat()
        self.iniciada_en  = None
        self.terminada_en = None
        self.asyncio_task = None  # referencia para poder cancelarla

# estado global de la app
cola: asyncio.Queue = None
tareas: dict[str, Tarea] = {}

def inicializar_cola():
    global cola
    cola = asyncio.Queue()
