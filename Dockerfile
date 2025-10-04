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

# Expone el puerto que la aplicación usará dentro del contenedor
EXPOSE 10000

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Render pasará la variable $PORT con el valor 10000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]