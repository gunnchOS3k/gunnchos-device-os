# Cloud / fleet runnable DEV plane

Local compose stack for identity, enrollment, sync, saves, matchmaking metadata,
OTA metadata, telemetry, fleet, diagnostics, plus an OpenTelemetry Collector.

## Claim boundary

**DEV only.** Not a production multi-tenant cloud, not campus MDM, not carrier-certified.
Use `DEV_*` enrollment tokens only.

## Quick start (Docker)

```bash
docker compose -f deploy/cloud_dev_plane/docker-compose.yml up --build
curl -s http://127.0.0.1:8100/v1/inventory | python3 -m json.tool
```

## Quick start (no Docker)

```bash
PYTHONPATH=.:src python3 -m gunnchos_device_os.cloud_dev_plane
# or: make cloud-dev-plane
```

## Modes

Send `X-Gunnchos-Mode: local|disconnected|campus_edge|cloud` (or JSON `mode`).

| Mode | Allowed surfaces |
| --- | --- |
| `local` | identity, enrollment, sync, saves, matchmaking, telemetry, update_metadata (+ fleet/diagnostics via gateway) |
| `disconnected` | identity, saves (+ local diagnostics); sync/telemetry/enrollment blocked |
| `campus_edge` | full online surface |
| `cloud` | full online surface |

Outage survival: client queues writes locally and `resync()` drains after reconnect.

## Ports

| Service | Port |
| --- | ---: |
| gateway | 8100 |
| identity | 8101 |
| enrollment | 8102 |
| sync | 8103 |
| saves | 8104 |
| matchmaking | 8105 |
| ota_metadata | 8106 |
| telemetry | 8107 |
| fleet | 8108 |
| diagnostics | 8109 |
| otel OTLP HTTP/gRPC | 4318 / 4317 |
