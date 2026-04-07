import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Lista archivos de un directorio.")
    parser.add_argument("directorio", nargs="?", default=".", help="Directorio a listar")
    parser.add_argument("-a", "--all", action="store_true", help="Incluir archivos ocultos")
    parser.add_argument("--extension", help="Filtrar por extensión (ej: .py)")

    args = parser.parse_args()

    if not os.path.isdir(args.directorio):
        print(f"Error: '{args.directorio}' no es un directorio válido")
        sys.exit(1)

    archivos = os.listdir(args.directorio)
    archivos.sort()

    for archivo in archivos:
        if not args.all and archivo.startswith("."):
            continue
        if args.extension and not archivo.endswith(args.extension):
            continue
        ruta = os.path.join(args.directorio, archivo)
        if os.path.isdir(ruta):
            print(f"{archivo}/")
        else:
            print(archivo)

    sys.exit(0)

main()
