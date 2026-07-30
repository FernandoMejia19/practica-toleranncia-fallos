FROM nginx:alpine

# Copiar configuración de Nginx (desde el contexto de la raíz)
COPY gateway/nginx.conf /etc/nginx/nginx.conf

# Copiar los archivos estáticos del frontend
# Nota: Para construir esta imagen, ejecute el build desde la raíz del proyecto:
# docker build -t api-gateway:latest -f gateway/Dockerfile .
COPY FrontEnd/ /usr/share/nginx/html/