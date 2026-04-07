import sys

def main():
    if len(sys.argv) < 2:
        print("Suma: 0")
        sys.exit(0)
    
    total = 0
    for arg in sys.argv[1:]:
        try:
            total += float(arg)
        except ValueError:
            print(f"Error: '{arg}' no es un número válido")
            sys.exit(1)
    
    if total == int(total):
        print(f"Suma: {int(total)}")
    else:
        print(f"Suma: {total}")
    
    sys.exit(0)

main()
