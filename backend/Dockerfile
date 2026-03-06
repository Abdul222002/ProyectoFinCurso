# ==========================================
# Backend FastAPI - Dockerfile
# ==========================================
FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc en el contenedor
ENV PYTHONDONTWRITEBYTECODE 1
# Evitar que Python bufferee los mensajes estándar (stdin, stdout)
ENV PYTHONUNBUFFERED 1

# Establecer directorio de trabajo en /backend
WORKDIR /backend

# Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt .

# Instalar las dependencias sin cache para que la imagen pese menos
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del backend
COPY . .

# Exponer el puerto en el que correrá Uvicorn
EXPOSE 8000

# Comando para ejecutar la aplicación
# Cambia 'app.main:app' si tu punto de entrada está en otro lugar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
