# FULL PRODUCT CONTINUATION IV — runnable cloud/fleet/security DEV plane

## Verdict

In-process and compose-backed **DEV** control-plane surfaces now run as real local HTTP
services (stdlib), with mode gates, outage/resync, OTLP round-trip, and security-ops hooks.
Still **not** a production cloud, campus MDM, or carrier-certified stack.

## Service inventory

| Service | Role env | Default port | Routes (gateway also hosts all) |
| --- | --- | ---: | --- |
| gateway | `gateway` | 8100 | `/v1/*` aggregate + `/v1/inventory` |
| identity | `identity` | 8101 | `/v1/identity/*` |
| enrollment | `enrollment` | 8102 | `/v1/enrollment/submit` |
| sync | `sync` | 8103 | `/v1/sync/*` |
| saves | `saves` | 8104 | `/v1/saves/*` |
| matchmaking | `matchmaking` | 8105 | `/v1/matchmaking/*` (metadata only) |
| ota_metadata | `ota_metadata` | 8106 | `/v1/ota/metadata*` |
| telemetry | `telemetry` | 8107 | `/v1/telemetry/emit` |
| fleet | `fleet` | 8108 | `/v1/fleet/*` |
| diagnostics | `diagnostics` | 8109 | `/v1/diagnostics/*` |
| otel-collector | compose | 4317/4318 | OTLP gRPC/HTTP |

Compose: `deploy/cloud_dev_plane/docker-compose.yml`  
Module: `python -m gunnchos_device_os.cloud_dev_plane`

## Modes

| Mode | Behavior |
| --- | --- |
| `LOCAL` | Full online surface against local store |
| `DISCONNECTED` | identity + saves (+ local diagnostics); blocks sync/telemetry/enrollment/matchmaking/OTA/fleet |
| `CAMPUS_EDGE` | Full online surface (campus adapter label) |
| `CLOUD` | Full online surface (cloud adapter label) |

Header: `X-Gunnchos-Mode` or JSON `mode`.

## Tokens

| Token | Status |
| --- | --- |
| `DEV_ENROLLMENT_TOKEN` / any `DEV_*` | Accepted in DEV plane |
| Non-`DEV_` enrollment tokens | Rejected (403) |
| Production MDM / carrier secrets | Forbidden |

## OTEL

- Conventions: `gunnchos.service`, `gunnchos.mode`, `gunnchos.device.id`, `gunnchos.realm`, span names `gunnchos.*`
- Privacy redaction before export (`privacy_redaction.py`) + collector attribute deletes
- Local collector config: `deploy/cloud_dev_plane/otel-collector-config.yaml`

## Security ops (DEV)

- SAST hook: `security/dev_ops/sast_hook.py`
- Abuse suite: `security/dev_ops/abuse_suite.py`
- SBOM/provenance: `scripts/generate_cloud_dev_plane_sbom.py` → `results/cloud_dev_plane/`
- Incident runbooks: `docs/security/INCIDENT_RUNBOOKS_DEV.md`
- Fuzz starters extended in `tests/test_adversarial_fuzz_starters.py`

## Tests

```bash
PYTHONPATH=.:src pytest -q \
  tests/test_cloud_dev_plane_modes.py \
  tests/test_cloud_dev_plane_outage_resync.py \
  tests/test_cloud_dev_plane_otel.py \
  tests/test_cloud_dev_plane_security_ops.py \
  tests/test_adversarial_fuzz_starters.py \
  tests/test_cloud_edge_services.py
```

Or: `make cloud-dev-plane-test`
