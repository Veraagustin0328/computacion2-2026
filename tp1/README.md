# Trabajo Practico N1 
- Computacion II 
- Agustin Vera

## Monitor de Procesos y Threads

Este proyecto es un monitor interactivo en tiempo real para Linux (estilo `htop`), enfocado en mostrar la anatomia interna de los procesos y sus hilos. La informacion se extrae leyendo directamente del sistema de archivos `/proc`, sin usar librerias de alto nivel como `psutil`.

El proyecto fue desarrollado y probado localmente en un entorno Linux (Ubuntu sobre WSL2) y esta completamente contenerizado en Docker para su entrega y ejecucion. El sistema esta disenado como una arquitectura multiproceso: un recolector central busca los procesos activos, 7 analizadores en paralelo extraen metricas especificas, un agregador centraliza el snapshot en memoria compartida y la interfaz TUI (hecha con `rich`) permite navegar por los datos en tiempo real.

---

## 1. Como correr el proyecto

El proyecto esta preparado para ejecutarse dentro de un entorno Docker.

```bash
# Clonar el repo
git clone https://github.com/Veraagustin0328/computacion2-2026.git
cd computacion2-2026/tp1

# Levantar con docker-compose
docker compose up --build
```

### Atajos de teclado en la TUI

| Tecla | Accion |
|-------|--------|
| `1` a `7` o `r/m/f/t/s/p/g` | Cambiar de vista |
| Flechas arriba/abajo | Navegar por la lista de procesos |
| `Enter` | Fijar (pin) un proceso en el panel inferior |
| `c` | Alternar criterio de ordenamiento (CPU%, RSS, PID) |
| `+` / `-` | Ajustar intervalo de refresco de la vista actual |
| `q` | Salir de forma limpia |

---

## 2. Arquitectura del Sistema

Para organizar el trabajo y evitar cuellos de botella, dividimos la logica en componentes independientes que se comunican entre si:



      ┌─────────────────────────────────────────┐
      │             SNAPSHOT GLOBAL             │
      │        (multiprocessing.Manager)        │
      │  ┌───────────────────────────────────┐  │
      │  │ "resumen", "memoria", "fds", ...  │  │
      │  └───────────────────────────────────┘  │
      └─────────▲─────────────────────▲─────────┘
                │ escriben            │ lee

┌───────────────────┼──────────┬──────────┴─────────┐
│ │ │ │
│ Recolector Resumen Memoria ... Display │
│ (pids) cada 2s cada 3s TUI │
│ │ Queue ▲ ▲ │ │
│ └─────────────┴──────────┘ │ │
└──────────────────────────────────────────────







**Modulos principales:**

- `main.py`: Punto de entrada. Inicializa la memoria compartida, arranca los procesos hijos y gestiona el apagado limpio al recibir senales.
- `procfs.py`: Centraliza todas las funciones para leer y parsear archivos de `/proc`.
- `recolector.py`: Lista los PIDs en `/proc` y los reparte a los analizadores via Queue.
- `analizadores/`: 7 procesos independientes que corren en bucle a su propio ritmo.
- `display.py`: La interfaz TUI que consulta el snapshot y refresca la pantalla.
- `senales.py`: Maneja las senales que recibe el monitor (SIGINT, SIGUSR1, SIGHUP, etc.).

---

## 3. Decisiones de Diseno e IPC

### Por que multiproceso y no threads?

El GIL de Python impide que varios hilos ejecuten codigo en paralelo real. Como el monitor tiene que estar constantemente leyendo y parseando archivos de `/proc`, un esquema multithread se trabaria. Con `multiprocessing.Process` cada analizador corre en un proceso separado de Linux, aprovechando los distintos nucleos de la CPU.

### Eleccion de primitivas de IPC

- **`multiprocessing.Queue`**: Para que el recolector le pase las listas de PIDs a los analizadores de forma segura.
- **`multiprocessing.Manager.dict`**: Para el snapshot global, necesitabamos que todos los analizadores pudieran actualizar su clave sin pisarse. El Manager sincroniza los accesos evitando race conditions.
- **`multiprocessing.Value`**: Los intervalos de refresco se pueden cambiar desde la TUI con `+` y `-`. Se guardan en variables `Value` para que la TUI los modifique y el analizador lea el nuevo valor en su siguiente iteracion.

### Evitando Race Conditions

Cada analizador es dueno exclusivo de su propia clave en el snapshot (`resumen`, `memoria`, `fds`, etc.). Los analizadores parsean todos los datos localmente y al final hacen la actualizacion en el `Manager.dict` en un solo paso.

### Intervalos por defecto

- **Resumen, Threads y Sistema (2s)**: Las vistas mas consultadas para ver CPU y procesos activos.
- **Memoria (3s)**: Cambia seguido pero no necesita refresco tan agresivo.
- **File Descriptors (5s)**: Hacer `os.readlink()` sobre cada descriptor de cientos de procesos es costoso.
- **Senales y Scheduling (10s)**: Estos datos casi nunca cambian durante la ejecucion de un proceso.

---

## 4. Conceptos de la materia aplicados

- **Archivos virtuales `/proc` (Clase 3)**: `/proc` no ocupa espacio en disco, es una interfaz del kernel. En `procfs.py` parseamos `/proc/<pid>/stat` (campo 3 = estado, campos 14-15 = jiffies de CPU) y `/proc/<pid>/status`.
- **Procesos Zombie (Clase 4)**: Detectamos procesos en estado `Z`. Ocurren cuando un hijo termino pero el padre no llamo a `wait()` para leer su codigo de retorno.
- **Threads como LWPs (Clase 10)**: En Linux los hilos son Light-Weight Processes. En la vista de hilos recorremos `/proc/<pid>/task/`, donde cada subcarpeta es un TID.
- **Mascaras Bitwise (Clase 6)**: Para mostrar senales bloqueadas de forma legible, tomamos los hexadecimales de `SigBlk`, `SigCgt`, etc. y aplicamos operaciones de bits para mapear que senal esta activa.

---

## 5. Manejo de senales del monitor

| Senal | Accion |
|-------|--------|
| `SIGINT` / `SIGTERM` | Apagado limpio: cierra analizadores y libera memoria |
| `SIGHUP` | Recarga `config.json` con nuevos intervalos |
| `SIGUSR1` | Guarda snapshot en `dump_<timestamp>.json` |
| `SIGUSR2` | Toggle modo verbose |

```bash
# Obtener el PID del proceso principal
PID=$(pgrep -f "src/main.py")

# Generar dump
kill -SIGUSR1 $PID

# Recargar config
kill -SIGHUP $PID
```

---

## 6. Limitaciones conocidas

- **Procesos muy cortos**: Si un proceso nace y muere antes de que el analizador lo lea, se lanza un `FileNotFoundError` que capturamos para que el monitor no se caiga.
- **Permisos**: Sin permisos de root no se pueden leer los FDs ni la memoria de procesos de otros usuarios.
- **TUI en WSL2 + Docker**: WSL2 tiene limitaciones con pseudo-terminales en Docker. El sistema corre correctamente pero la navegacion por teclado dentro del contenedor requiere Linux nativo.

---

## 7. Lo que aprendi haciendo el TP

Hacer este monitor me ayudo a bajar a tierra muchos conceptos que hasta ahora solo habia visto en diapositivas. Ver como se comporta `/proc` en un sistema vivo, entender que en Linux los hilos son LWPs administrados por la misma estructura que los procesos, y lidiar con problemas reales de concurrencia e IPC fue bastante util. Tambien aprecie la importancia de hacer un shutdown limpio para no dejar procesos zombies colgados al cerrar la aplicacion.
EOF
