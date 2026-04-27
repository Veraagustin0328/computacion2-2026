#!/usr/bin/env python3
"""Mini-shell con redirección."""
import os
import sys

def parsear_linea(linea):
    partes = linea.split()
    comando = partes[0] if partes else None
    args = []
    archivo_salida = None
    archivo_entrada = None

    i = 1
    while i < len(partes):
        if partes[i] == ">":
            archivo_salida = partes[i + 1]
            i += 2
        elif partes[i] == ">>":
            archivo_salida = ("append", partes[i + 1])
            i += 2
        elif partes[i] == "<":
            archivo_entrada = partes[i + 1]
            i += 2
        else:
            args.append(partes[i])
            i += 1

    return comando, args, archivo_salida, archivo_entrada

def cmd_cd(args):
    if not args:
        destino = os.environ.get("HOME", "/")
    else:
        destino = args[0]
    try:
        os.chdir(destino)
    except OSError as e:
        print(f"cd: {e}")

def ejecutar(comando, args, archivo_salida=None, archivo_entrada=None):
    pid = os.fork()

    if pid == 0:
        if archivo_salida:
            if isinstance(archivo_salida, tuple) and archivo_salida[0] == "append":
                fd = os.open(archivo_salida[1], os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o644)
            else:
                fd = os.open(archivo_salida, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            os.dup2(fd, 1)
            os.close(fd)

        if archivo_entrada:
            fd = os.open(archivo_entrada, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)

        try:
            os.execvp(comando, [comando] + args)
        except OSError as e:
            print(f"Error: {e}", file=sys.stderr)
            os._exit(127)
    else:
        _, status = os.wait()
        return os.WEXITSTATUS(status)

def main():
    internos = {"cd": cmd_cd}

    while True:
        try:
            cwd = os.getcwd()
            linea = input(f"minish:{cwd}$ ")
        except EOFError:
            print("\nChau!")
            break

        linea = linea.strip()
        if not linea:
            continue

        if linea == "exit":
            break

        comando, args, salida, entrada = parsear_linea(linea)
        if comando:
            if comando in internos:
                internos[comando](args)
            else:
                ejecutar(comando, args, salida, entrada)

if __name__ == "__main__":
    main()
