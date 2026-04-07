import argparse
import sys

def buscar_en_lineas(lineas, patron, ignorar_case, invertir, contar, mostrar_numero, prefijo=""):
    coincidencias = 0
    for i, linea in enumerate(lineas, 1):
        linea = linea.rstrip("\n")
        texto = linea.lower() if ignorar_case else linea
        patron_buscar = patron.lower() if ignorar_case else patron
        encontrado = patron_buscar in texto

        if invertir:
            encontrado = not encontrado

        if encontrado:
            coincidencias += 1
            if not contar:
                if prefijo:
                    if mostrar_numero:
                        print(f"{prefijo}:{i}: {linea}")
                    else:
                        print(f"{prefijo}: {linea}")
                else:
                    if mostrar_numero:
                        print(f"{i}: {linea}")
                    else:
                        print(linea)

    return coincidencias

def main():
    parser = argparse.ArgumentParser(description="Busca patrones en archivos de texto.")
    parser.add_argument("patron", help="Patrón a buscar")
    parser.add_argument("archivos", nargs="*", help="Archivos donde buscar")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignorar mayúsculas/minúsculas")
    parser.add_argument("-n", "--line-number", action="store_true", help="Mostrar número de línea")
    parser.add_argument("-c", "--count", action="store_true", help="Mostrar solo conteo de coincidencias")
    parser.add_argument("-v", "--invert", action="store_true", help="Mostrar líneas que NO coinciden")

    args = parser.parse_args()

    multiples = len(args.archivos) > 1

    if not args.archivos:
        if not sys.stdin.isatty():
            lineas = sys.stdin.readlines()
            buscar_en_lineas(lineas, args.patron, args.ignore_case, args.invert, args.count, args.line_number)
        else:
            print("Error: especificá al menos un archivo o usá stdin")
            sys.exit(1)
    else:
        total = 0
        for archivo in args.archivos:
            try:
                with open(archivo, "r") as f:
                    lineas = f.readlines()
                count = buscar_en_lineas(lineas, args.patron, args.ignore_case, args.invert, args.count, args.line_number or multiples, archivo if multiples else "")
                if args.count:
                    print(f"{archivo}: {count} coincidencias")
                total += count
            except FileNotFoundError:
                print(f"Error: no se puede leer '{archivo}'")
                sys.exit(1)

        if args.count and multiples:
            print(f"Total: {total} coincidencias")

    sys.exit(0)

main()
