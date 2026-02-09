FROM python:3.11-slim

# Usamos --no-install-recommends para evitar paquetes basura (como la interfaz de LibreOffice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-java-common \
    default-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Aprovechar el caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear el directorio de uploads
RUN mkdir -p uploads
ENV HOME=/tmp
EXPOSE 10000

# Usamos un solo worker para no duplicar el consumo de RAM de Python
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000", "--workers", "1"]