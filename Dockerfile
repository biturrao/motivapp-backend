# Usar una imagen base de Python oficial y ligera
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos
COPY ./requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Azure App Service usa el puerto 8000 por defecto
EXPOSE 8000

# Copiar y dar permisos al script de inicio
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Azure Web App ejecutará este comando
CMD ["/app/startup.sh"]