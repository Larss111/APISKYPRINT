FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre-headless \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# OPTIMIZACIÓN: Copiar solo requirements primero para usar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del proyecto
COPY . .

# Crear el directorio de uploads con permisos correctos
RUN mkdir -p uploads && chmod 777 uploads

# Variable de entorno para que LibreOffice no de problemas de perfil
ENV HOME=/tmp

# Exponer el puerto
EXPOSE 10000

# Comando para ejecutar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]