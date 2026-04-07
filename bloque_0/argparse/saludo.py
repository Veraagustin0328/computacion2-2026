import sys

def main():
    if len(sys.argv) < 2:
        print("Uso: saludo.py <nombre>")
        sys.exit(1)
    
    nombre = " ".join(sys.argv[1:])
    print(f"Hola, {nombre}!")
    sys.exit(0)

main()
