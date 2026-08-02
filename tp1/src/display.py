import time
import os
import sys
import threading
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

console = Console()

VISTAS = {
    '1': 'resumen',
    '2': 'memoria',
    '3': 'fds',
    '4': 'threads',
    '5': 'senales',
    '6': 'scheduling',
    '7': 'sistema',
    'r': 'resumen',
    'm': 'memoria',
    'f': 'fds',
    't': 'threads',
    's': 'senales',
    'p': 'scheduling',
    'g': 'sistema',
}

class Display:
    def __init__(self, snapshot, intervalos):
        self.snapshot = snapshot
        self.intervalos = intervalos
        self.vista_activa = 'resumen'
        self.proceso_seleccionado = None
        self.proceso_pinado = None
        self.filtro_nombre = None
        self.filtro_usuario = None
        self.orden = 'cpu'
        self.ejecutando = True
        self.indice_seleccion = 0

    def obtener_procesos_ordenados(self):
        if "resumen" not in self.snapshot:
            return []
        datos = self.snapshot["resumen"].get("datos", {})
        procesos = list(datos.values())
        if self.filtro_nombre:
            procesos = [p for p in procesos if self.filtro_nombre.lower() in p.get("nombre", "").lower()]
        if self.filtro_usuario:
            procesos = [p for p in procesos if p.get("uid", "") == self.filtro_usuario]
        if self.orden == 'cpu':
            procesos.sort(key=lambda x: x.get('cpu_pct', 0), reverse=True)
        elif self.orden == 'rss':
            procesos.sort(key=lambda x: x.get('rss_kb', 0), reverse=True)
        elif self.orden == 'pid':
            procesos.sort(key=lambda x: x.get('pid', 0))
        return procesos

    def tabla_procesos(self):
        tabla = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan", expand=True)
        tabla.add_column("PID", width=7)
        tabla.add_column("NOMBRE", width=20)
        tabla.add_column("EST", width=4)
        tabla.add_column("CPU%", width=7)
        tabla.add_column("RSS(KB)", width=9)
        tabla.add_column("THR", width=4)
        tabla.add_column("COMANDO", ratio=1)

        procesos = self.obtener_procesos_ordenados()

        for i, proc in enumerate(procesos[:20]):
            seleccionado = i == self.indice_seleccion
            pinado = proc.get('pid') == self.proceso_pinado
            estilo = ""
            if pinado:
                estilo = "bold yellow"
            elif seleccionado:
                estilo = "bold white on blue"

            estado = proc.get('estado', '?')
            color_estado = {
                'R': '[green]R[/green]',
                'S': '[blue]S[/blue]',
                'D': '[red]D[/red]',
                'Z': '[red]Z[/red]',
                'T': '[yellow]T[/yellow]',
            }.get(estado, estado)

            cpu = proc.get('cpu_pct', 0)
            cpu_str = f"[red]{cpu}[/red]" if cpu > 50 else f"[green]{cpu}[/green]"

            tabla.add_row(
                str(proc.get('pid', '')),
                proc.get('nombre', '')[:20],
                color_estado,
                cpu_str,
                str(proc.get('rss_kb', 0)),
                str(proc.get('threads', 1)),
                (proc.get('cmdline', '') or proc.get('nombre', ''))[:50],
                style=estilo,
            )
        return tabla

    def panel_resumen(self, pid):
        if not pid or "resumen" not in self.snapshot:
            return Panel("Selecciona un proceso", title="Resumen")
        datos = self.snapshot["resumen"].get("datos", {})
        proc = datos.get(pid, {})
        if not proc:
            return Panel("Sin datos", title="Resumen")
        texto = Text()
        texto.append(f"PID: {proc.get('pid')}\n", style="bold")
        texto.append(f"PPID: {proc.get('ppid')}\n")
        texto.append(f"Estado: {proc.get('estado')}\n")
        texto.append(f"CPU%: {proc.get('cpu_pct')}%\n")
        texto.append(f"RSS: {proc.get('rss_kb')} KB\n")
        texto.append(f"Threads: {proc.get('threads')}\n")
        texto.append(f"UID: {proc.get('uid')}\n")
        texto.append(f"Comando: {proc.get('cmdline', proc.get('nombre', ''))}\n")
        return Panel(texto, title=f"Resumen - PID {pid}")

    def panel_memoria(self, pid):
        if not pid or "memoria" not in self.snapshot:
            return Panel("Sin datos de memoria", title="Memoria")
        datos = self.snapshot["memoria"].get("datos", {})
        proc = datos.get(pid, {})
        if not proc:
            return Panel("Sin datos", title="Memoria")
        texto = Text()
        texto.append(f"VmSize:  {proc.get('vm_size', 0)} KB\n")
        texto.append(f"VmRSS:   {proc.get('vm_rss', 0)} KB\n")
        texto.append(f"VmData:  {proc.get('vm_data', 0)} KB\n")
        texto.append(f"VmStk:   {proc.get('vm_stk', 0)} KB\n")
        texto.append(f"VmExe:   {proc.get('vm_exe', 0)} KB\n")
        texto.append(f"VmLib:   {proc.get('vm_lib', 0)} KB\n")
        texto.append(f"VmHWM:   {proc.get('vm_hwm', 0)} KB\n")
        texto.append(f"VmSwap:  {proc.get('vm_swap', 0)} KB\n")
        texto.append(f"\nPage faults:\n")
        texto.append(f"  Minor: {proc.get('minor_faults', 0)}\n")
        texto.append(f"  Major: {proc.get('major_faults', 0)}\n")
        texto.append(f"\nSegmentos:\n")
        for seg, kb in proc.get('segmentos', {}).items():
            texto.append(f"  {seg}: {kb} KB\n")
        return Panel(texto, title=f"Memoria - PID {pid}")

    def panel_fds(self, pid):
        if not pid or "fds" not in self.snapshot:
            return Panel("Sin datos de FDs", title="File Descriptors")
        datos = self.snapshot["fds"].get("datos", {})
        proc = datos.get(pid, {})
        if not proc:
            return Panel("Sin datos (sin permisos?)", title="File Descriptors")
        texto = Text()
        texto.append(f"Total FDs: {proc.get('total', 0)}\n")
        texto.append(f"Por tipo: {proc.get('tipos', {})}\n\n")
        for fd in proc.get('fds', [])[:15]:
            texto.append(f"  fd{fd['fd']}: [{fd['tipo']}] {fd['destino']}\n")
        return Panel(texto, title=f"File Descriptors - PID {pid}")

    def panel_threads(self, pid):
        if not pid or "threads" not in self.snapshot:
            return Panel("Sin datos de threads", title="Threads")
        datos = self.snapshot["threads"].get("datos", {})
        proc = datos.get(pid, {})
        if not proc:
            return Panel("Sin datos", title="Threads")
        texto = Text()
        texto.append(f"Total threads: {proc.get('total', 0)}\n\n")
        for t in proc.get('threads', []):
            texto.append(f"  TID {t['tid']}: {t['nombre']} | {t['estado']} | CPU: {t['cpu_pct']}%\n")
            texto.append(f"    ctx_vol: {t['ctx_voluntarios']} | ctx_invol: {t['ctx_involuntarios']}\n")
        return Panel(texto, title=f"Threads - PID {pid}")

    def panel_senales(self, pid):
        if not pid or "senales" not in self.snapshot:
            return Panel("Sin datos de señales", title="Señales")
        datos = self.snapshot["senales"].get("datos", {})
        proc = datos.get(pid, {})
        if not proc:
            return Panel("Sin datos", title="Señales")
        texto = Text()
        texto.append(f"Bloqueadas: {', '.join(proc.get('bloqueadas', []))}\n\n")
        texto.append(f"Ignoradas:  {', '.join(proc.get('ignoradas', []))}\n\n")
        texto.append(f"Capturadas: {', '.join(proc.get('capturadas', []))}\n\n")
        texto.append(f"Pendientes proceso: {', '.join(proc.get('pendientes_proceso', []))}\n")
        texto.append(f"Pendientes grupo:   {', '.join(proc.get('pendientes_grupo', []))}\n")
        return Panel(texto, title=f"Señales - PID {pid}")

    def panel_scheduling(self, pid):
        if not pid or "scheduling" not in self.snapshot:
            return Panel("Sin datos de scheduling", title="Scheduling")
        datos = self.snapshot["scheduling"].get("datos", {})
        proc = datos.get(pid, {})
        if not proc:
            return Panel("Sin datos", title="Scheduling")
        texto = Text()
        texto.append(f"Nice:        {proc.get('nice', 0)}\n")
        texto.append(f"Priority:    {proc.get('priority', 0)}\n")
        texto.append(f"Politica:    {proc.get('politica', 'N/A')}\n")
        texto.append(f"RT Priority: {proc.get('rt_priority', 0)}\n")
        texto.append(f"CPU Affinity: {proc.get('cpu_affinity', 'N/A')}\n")
        texto.append(f"\nContext switches:\n")
        texto.append(f"  Voluntarios:   {proc.get('ctx_voluntarios', 0)}\n")
        texto.append(f"  Involuntarios: {proc.get('ctx_involuntarios', 0)}\n")
        texto.append(f"\nSID:  {proc.get('sid', 0)}\n")
        texto.append(f"PGID: {proc.get('pgid', 0)}\n")
        return Panel(texto, title=f"Scheduling - PID {pid}")

    def panel_sistema(self):
        if "sistema" not in self.snapshot:
            return Panel("Sin datos del sistema", title="Sistema")
        datos = self.snapshot["sistema"].get("datos", {})
        cpu = datos.get("cpu", {})
        mem = datos.get("memoria", {})
        load = datos.get("loadavg", {})
        procs = datos.get("procesos", {})
        texto = Text()
        texto.append("=== CPU ===\n", style="bold cyan")
        texto.append(f"  Total: {cpu.get('total_pct', 0)}%\n")
        texto.append(f"  User:  {cpu.get('user', 0)}%\n")
        texto.append(f"  System:{cpu.get('system', 0)}%\n")
        texto.append(f"  Idle:  {cpu.get('idle', 0)}%\n")
        texto.append(f"  IOWait:{cpu.get('iowait', 0)}%\n")
        texto.append("\n=== MEMORIA ===\n", style="bold cyan")
        total = mem.get('total_kb', 0) // 1024
        usado = mem.get('usado_kb', 0) // 1024
        libre = mem.get('libre_kb', 0) // 1024
        texto.append(f"  Total:     {total} MB\n")
        texto.append(f"  Usado:     {usado} MB\n")
        texto.append(f"  Libre:     {libre} MB\n")
        texto.append(f"  Swap tot:  {mem.get('swap_total_kb', 0)//1024} MB\n")
        texto.append(f"  Swap libre:{mem.get('swap_libre_kb', 0)//1024} MB\n")
        texto.append("\n=== LOAD AVERAGE ===\n", style="bold cyan")
        texto.append(f"  1min:  {load.get('1min', 0)}\n")
        texto.append(f"  5min:  {load.get('5min', 0)}\n")
        texto.append(f"  15min: {load.get('15min', 0)}\n")
        texto.append("\n=== PROCESOS ===\n", style="bold cyan")
        texto.append(f"  Total:   {procs.get('total', 0)}\n")
        texto.append(f"  Zombies: {procs.get('zombies', 0)}\n")
        for estado, cant in procs.get('por_estado', {}).items():
            texto.append(f"  {estado}: {cant}\n")
        return Panel(texto, title="Sistema Global")

    def obtener_panel_detalle(self, pid):
        if self.vista_activa == 'resumen':
            return self.panel_resumen(pid)
        elif self.vista_activa == 'memoria':
            return self.panel_memoria(pid)
        elif self.vista_activa == 'fds':
            return self.panel_fds(pid)
        elif self.vista_activa == 'threads':
            return self.panel_threads(pid)
        elif self.vista_activa == 'senales':
            return self.panel_senales(pid)
        elif self.vista_activa == 'scheduling':
            return self.panel_scheduling(pid)
        elif self.vista_activa == 'sistema':
            return self.panel_sistema()
        return Panel("Vista no implementada")

    def barra_estado(self):
        intervalo = self.intervalos.get(self.vista_activa)
        val = intervalo.value if intervalo else 0
        filtro_str = ""
        if self.filtro_nombre:
            filtro_str = f" | filtro: {self.filtro_nombre}"
        orden_str = f"orden: {self.orden}"
        return Text(
            f"Vista: [{self.vista_activa}] | intervalo: {val}s | {orden_str}{filtro_str} | "
            f"1-7:vista | flechas:navegar | Enter:pin | c:orden | q:salir",
            style="bold on dark_blue"
        )

    def renderizar(self):
        procesos = self.obtener_procesos_ordenados()
        pid = self.proceso_pinado
        if not pid and procesos and self.indice_seleccion < len(procesos):
            pid = procesos[self.indice_seleccion].get('pid')
        layout = Layout()
        layout.split_column(
            Layout(name="estado", size=1),
            Layout(name="principal", ratio=1),
            Layout(name="detalle", ratio=1),
        )
        layout["estado"].update(self.barra_estado())
        layout["principal"].update(Panel(self.tabla_procesos(), title="Procesos"))
        layout["detalle"].update(self.obtener_panel_detalle(pid))
        return layout

def leer_teclado(display):
    import tty
    import termios
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except termios.error:
        print("[Display] No hay terminal interactiva, navegacion deshabilitada")
        return
    try:
        tty.setraw(fd)
        while display.ejecutando:
            ch = sys.stdin.read(1)
            if ch == 'q':
                display.ejecutando = False
                break
            elif ch in VISTAS:
                display.vista_activa = VISTAS[ch]
            elif ch == 'c':
                ordenes = ['cpu', 'rss', 'pid']
                idx = ordenes.index(display.orden)
                display.orden = ordenes[(idx + 1) % len(ordenes)]
            elif ch == '+':
                if display.vista_activa in display.intervalos:
                    display.intervalos[display.vista_activa].value += 0.5
            elif ch == '-':
                if display.vista_activa in display.intervalos:
                    val = display.intervalos[display.vista_activa].value
                    display.intervalos[display.vista_activa].value = max(0.5, val - 0.5)
            elif ch == '\r':
                procesos = display.obtener_procesos_ordenados()
                if procesos and display.indice_seleccion < len(procesos):
                    pid = procesos[display.indice_seleccion].get('pid')
                    if display.proceso_pinado == pid:
                        display.proceso_pinado = None
                    else:
                        display.proceso_pinado = pid
            elif ch == '\x1b':
                seq = sys.stdin.read(2)
                procesos = display.obtener_procesos_ordenados()
                if seq == '[A':
                    display.indice_seleccion = max(0, display.indice_seleccion - 1)
                elif seq == '[B':
                    display.indice_seleccion = min(len(procesos) - 1, display.indice_seleccion + 1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def iniciar_display(snapshot, intervalos):
    display = Display(snapshot, intervalos)
    hilo_teclado = threading.Thread(target=leer_teclado, args=(display,), daemon=True)
    hilo_teclado.start()
    with Live(display.renderizar(), refresh_per_second=1, screen=False) as live:
        while display.ejecutando:
            time.sleep(1)
            live.update(display.renderizar())
    return display.ejecutando