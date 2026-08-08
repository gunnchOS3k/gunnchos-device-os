# Incident runbooks — cloud/fleet DEV plane

**Scope:** Local/dev compose and in-process DEV plane only. Not production IR.

## IR-DEV-01 — Suspected secret in telemetry buffer

1. Stop the affected service / gateway (`docker compose stop` or kill local process).
2. Inspect store JSON (`GUNNCHOS_STORE_PATH`) and OTEL file exporter output for plaintext tokens/emails.
3. Confirm privacy redaction path: `gunnchos_device_os/cloud_dev_plane/privacy_redaction.py`.
4. Rotate any `DEV_*` tokens used in the session; never introduce production secrets.
5. Re-run `python security/dev_ops/sast_hook.py` and `pytest -q tests/test_cloud_dev_plane_*.py`.
6. Record timeline in `results/cloud_dev_plane/` (DEV evidence only).

## IR-DEV-02 — Enrollment token abuse

1. Check `/v1/enrollment/submit` responses — non-`DEV_` tokens must return rejected/403.
2. Run abuse suite: `PYTHONPATH=.:src python security/dev_ops/abuse_suite.py`.
3. If a non-DEV token was accepted, treat as P0 regression; revert and open a draft PR fix.
4. Wipe enrollments from the shared store volume and restart compose.

## IR-DEV-03 — Mode capability bypass (DISCONNECTED syncing)

1. Reproduce with `X-Gunnchos-Mode: disconnected` against sync/telemetry/enrollment.
2. Expected: HTTP 403 from server and/or `PermissionError` from `DevPlaneClient`.
3. If sync delivered while disconnected, fail closed: stop gateway, patch `_MODE_CAPABILITIES` / server `_allow`.
4. Add a regression case under `tests/test_cloud_dev_plane_modes.py`.

## IR-DEV-04 — OTEL collector disk fill / PII in traces

1. Rotate `/var/log/otel/traces.json` volume; restart `otel-collector`.
2. Verify collector `attributes/gunnchos_privacy` deletes email/token keys.
3. Confirm client-side `redact_payload` before export.
4. Re-run `tests/test_cloud_dev_plane_otel.py`.

## IR-DEV-05 — Outage queue poison / resync storm

1. Inspect client outbox depth; if huge, clear process and restart with empty outbox.
2. Prefer `resync()` after connectivity restored; confirm partial failures remain queued.
3. Validate with `tests/test_cloud_dev_plane_outage_resync.py`.

## Tokens

| Token class | Allowed |
| --- | --- |
| `DEV_*` enrollment | Yes (DEV plane) |
| Production / carrier / school MDM secrets | **Never** |
