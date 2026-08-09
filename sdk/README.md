# gunnchOS Adopter SDK

Digital SDK for building apps against gunnchOS device roles, ring input, AI,
connectivity, and telemetry surfaces.

## Setup

```bash
cd sdk
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill placeholders only — never commit secrets
pytest -q
```

## Quick start

```python
from gunnchos_adopter_sdk import AdopterClient

client = AdopterClient(base_url="http://127.0.0.1:8080")
print(client.negotiate("app_manifest", "1.2.0"))
print(client.sample_device_role("student"))
print(client.sample_ring_input("tap"))
```

## Samples

- `samples/app_template` — minimal app manifest template
- `samples/ring_input` — ring gesture sample
- `samples/device_role` — role negotiation sample
- `samples/ai` — local-first AI sample
- `samples/connectivity` — bearer sample
- `samples/telemetry` — event sample

## Claims

This SDK is for digital/DEV integration. It does not include production signing
keys, store submission tooling, or carrier certification.
