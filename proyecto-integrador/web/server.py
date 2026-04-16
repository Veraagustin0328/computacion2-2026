from flask import Flask
import redis

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379)

@app.route('/')
def index():
    valor = r.get('contador_integrador')
    n = valor.decode() if valor else "0"
    return f"<h1>Proyecto Integrador</h1><p>El valor actual es: {n}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
