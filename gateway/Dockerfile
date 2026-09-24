# Etapa 1: build del frontend Vue con Vite
FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json ./

# Instalar dependencias incluyendo optional dependencies
RUN npm install --include=optional

COPY frontend/ ./

RUN npm run build


# Etapa 2: Nginx sirve el frontend
FROM nginx:alpine

COPY gateway/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
