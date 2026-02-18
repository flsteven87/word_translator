FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Startup script: replace port 80 with Zeabur's $PORT at runtime
RUN printf '#!/bin/sh\nset -e\nPORT="${PORT:-8080}"\nsed -i "s/listen 80;/listen ${PORT};/" /etc/nginx/nginx.conf\nexec nginx -g "daemon off;"\n' > /start.sh && \
    chmod +x /start.sh

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:${PORT:-8080}/health || exit 1

CMD ["/start.sh"]
