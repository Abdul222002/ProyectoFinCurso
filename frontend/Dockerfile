# ==========================================
# Etapa 1: Construcción (Build)
# ==========================================
FROM node:20-alpine AS build

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Variable de entorno para la URL del backend (se inyecta en build)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Construir la aplicación para producción
RUN npm run build

# ==========================================
# Etapa 2: Producción (Servidor Nginx)
# ==========================================
FROM nginx:alpine

# Copiar la configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar los archivos estáticos generados en la etapa de construcción anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Exponer el puerto dinámico
EXPOSE 80

# Usar envsubst para inyectar el puerto real de Railway en la configuración de Nginx antes de arrancar
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp && mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
