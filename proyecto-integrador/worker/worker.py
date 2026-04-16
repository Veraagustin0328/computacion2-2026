import redis
import time

# Se conecta al servicio llamado 'redis' definido en el compose
r = redis.Redis(host='redis', port=6379)

while True:
    valor = r.incr('contador_integrador')
    print(f"Worker: Incrementando contador a {valor}")
    time.sleep(1)
