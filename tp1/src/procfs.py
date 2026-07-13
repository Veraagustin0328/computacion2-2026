import os

def leer_archivo(path):
    # intento leer el archivo, si no tengo permisos o no existe lo ignoro
    try:
        with open(path, 'r', errors='replace') as f:
            return f.read()
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        return None

def listar_pids():
    # /proc tiene una carpeta por cada proceso activo, las que son numeros son PIDs
    pids = []
    for entrada in os.listdir('/proc'):
        if entrada.isdigit():
            pids.append(int(entrada))
    return sorted(pids)

def leer_stat(pid):
    # stat tiene todos los datos del proceso en una sola linea medio cruda
    # el problema es que el nombre puede tener espacios y esta entre parentesis
    contenido = leer_archivo(f'/proc/{pid}/stat')
    if not contenido:
        return None
    idx_inicio = contenido.find('(')
    idx_fin = contenido.rfind(')')
    nombre = contenido[idx_inicio+1:idx_fin]
    resto = contenido[idx_fin+2:].split()
    campos = [contenido[:idx_inicio].strip(), nombre] + resto
    return campos

def leer_status(pid):
    # status es mas legible que stat, tiene clave:valor
    contenido = leer_archivo(f'/proc/{pid}/status')
    if not contenido:
        return None
    resultado = {}
    for linea in contenido.splitlines():
        if ':' in linea:
            clave, valor = linea.split(':', 1)
            resultado[clave.strip()] = valor.strip()
    return resultado

def leer_cmdline(pid):
    # cmdline tiene el comando completo separado por caracteres nulos
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            data = f.read()
        return data.replace(b'\x00', b' ').decode(errors='replace').strip()
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        return None

if __name__ == "__main__":
    pids = listar_pids()
    print(f"Procesos encontrados: {len(pids)}")
    print(f"Primeros 5 PIDs: {pids[:5]}")

    pid = pids[0]
    print(f"\nStat de PID {pid}:")
    stat = leer_stat(pid)
    if stat:
        print(f"  Nombre: {stat[1]}")
        print(f"  Estado: {stat[2]}")

    print(f"\nStatus de PID {pid}:")
    status = leer_status(pid)
    if status:
        print(f"  VmRSS: {status.get('VmRSS', 'N/A')}")
        print(f"  Threads: {status.get('Threads', 'N/A')}")