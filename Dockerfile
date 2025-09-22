# Usar una imagen base de Python oficial y ligera
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos
COPY ./requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copiar el resto del código de la aplicación
# (En realidad, usaremos un volumen para desarrollo,
# pero esto es necesario para la construcción inicial y para producción)
COPY . .
