# DEV plane only — not a production image.
FROM python:3.11-slim
WORKDIR /app
COPY . /app
ENV PYTHONPATH=/app:/app/src
ENV GUNNCHOS_SERVICE=gateway
ENV GUNNCHOS_PORT=8100
ENV GUNNCHOS_STORE_PATH=/data/store.sqlite3
ENV GUNNCHOS_STORE_BACKEND=sqlite
ENV GUNNCHOS_MODE=local
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
EXPOSE 8100 8101 8102 8103 8104 8105 8106 8107 8108 8109
CMD ["python", "-m", "gunnchos_device_os.cloud_dev_plane"]
