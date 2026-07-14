FROM python:3.11-slim

WORKDIR /app

# instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copiar el codigo
COPY src/ ./src/

# el monitor necesita /proc del host, se monta en docker-compose
CMD ["python3", "src/main.py"]
