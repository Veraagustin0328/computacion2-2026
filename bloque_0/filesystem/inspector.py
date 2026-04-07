import argparse
import os
import stat
import pwd
import grp
import sys
from datetime import datetime

def formatear_fecha(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def formatear_tamanio(bytes):
    if bytes < 1024:
        return f"{bytes} bytes"
    else:
        kb = bytes / 1024
        return f"{bytes} bytes ({kb:.2f} KB)"

def obtener_tipo(modo, ruta):
    if stat.S_ISREG(modo):
        return "archivo regular"
    elif stat.S_ISDIR(modo):
        return "directorio"
    elif stat.S_ISLNK(modo):
        destino = os.readlink(ruta)
        return f"enlace simbólico -> {destino}"
    elif stat.S_ISCHR(modo):
        return "dispositivo de caracteres"
    elif stat.S_ISBLK(modo):
        return "dispositivo de bloques"
    elif stat.S_ISFIFO(modo):
        return "pipe (FIFO)"
    elif stat.S_ISSOCK(modo):
        return "socket"
    else:
        return "desconocido"

def formatear_permisos(modo):
    permisos = ""
    for quien in [(stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR),
                  (stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP),
                  (stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)]:
        permisos += "r" if modo & quien[0] else "-"
        permisos += "w" if modo & quien[1] else "-"
        permisos += "x" if modo & quien[2] else "-"
    octal = oct(modo & 0o777)[2:]
    return f"{permisos} ({octal})"

def main():
    parser = argparse.ArgumentParser(description="Muestra información detallada sobre un archivo.")
    parser.add_argument("ruta", help="Ruta del archivo a inspeccionar")
    args = parser.parse_args()

    if not os.path.exists(args.ruta) and not os.path.islink(args.ruta):
        print(f"Error: '{args.ruta}' no existe")
        sys.exit(1)

    info = os.lstat(args.ruta)
    modo = info.st_mode

    try:
        propietario = pwd.getpwuid(info.st_uid).pw_name
    except KeyError:
        propietario = str(info.st_uid)

    try:
        grupo = grp.getgrgid(info.st_gid).gr_name
    except KeyError:
        grupo = str(info.st_gid)

    print(f"Archivo: {args.ruta}")
    print(f"Tipo: {obtener_tipo(modo, args.ruta)}")
    print(f"Tamaño: {formatear_tamanio(info.st_size)}")
    print(f"Permisos: {formatear_permisos(modo)}")
    print(f"Propietario: {propietario} (uid: {info.st_uid})")
    print(f"Grupo: {grupo} (gid: {info.st_gid})")
    print(f"Inodo: {info.st_ino}")
    print(f"Enlaces duros: {info.st_nlink}")
    print(f"Última modificación: {formatear_fecha(info.st_mtime)}")
    print(f"Último acceso: {formatear_fecha(info.st_atime)}")
    print(f"Último cambio de estado: {formatear_fecha(info.st_ctime)}")

    if stat.S_ISDIR(modo):
        contenido = len(os.listdir(args.ruta))
        print(f"Contenido: {contenido} elementos")

    sys.exit(0)

main()
