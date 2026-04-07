import argparse
import secrets
import string
import sys

def main():
    parser = argparse.ArgumentParser(description="Generador de contraseñas seguras.")
    parser.add_argument("-n", "--length", type=int, default=12, help="Longitud de la contraseña (default: 12)")
    parser.add_argument("--no-symbols", action="store_true", help="Excluir símbolos especiales")
    parser.add_argument("--no-numbers", action="store_true", help="Excluir números")
    parser.add_argument("--count", type=int, default=1, help="Cantidad de contraseñas a generar (default: 1)")

    args = parser.parse_args()

    pool = string.ascii_letters
    if not args.no_numbers:
        pool += string.digits
    if not args.no_symbols:
        pool += "!@#$%&"

    if not pool:
        print("Error: no hay caracteres disponibles con las opciones seleccionadas")
        sys.exit(1)

    for _ in range(args.count):
        password = "".join(secrets.choice(pool) for _ in range(args.length))
        print(password)

    sys.exit(0)

main()
