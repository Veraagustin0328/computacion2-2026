FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
# El flag -u es para que Python no guarde los logs en buffer y los veas al instante
CMD ["python", "-u", "app.py"]

