FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx curl && rm -rf /var/lib/apt/lists/*
COPY artifact/launcher/dist /usr/share/nginx/html
RUN echo '{"status":"ok","artifact":"container_kiosk_prototype"}' > /usr/share/nginx/html/health.json
EXPOSE 80
HEALTHCHECK CMD curl -f http://localhost/health.json || exit 1
CMD ["nginx", "-g", "daemon off;"]
