# Lane H — exists vs stub (cloud / connectivity / fleet / security)

Honest inventory for FULL PRODUCT CONTINUATION III–IV.

| Surface | Status | Path | Notes |
| --- | --- | --- | --- |
| Radio capability profiles | **EXISTS (digital)** | `gunnchos_device_os/radio_capability.py` + device YAML `network:` | Profile-driven; rejects branded modem strings |
| Connectivity orchestrator | **EXISTS (digital)** | `gunnchos_device_os/connectivity_orchestrator.py` | Scores/handoff/faults; no live radio |
| Fleet enrollment / rings / canary / rollback | **SIM + DEV HTTP** | `fleet_ops.py` + `cloud_dev_plane` fleet routes | In-process ops sim + runnable DEV heartbeat/inventory |
| Health / diagnostics / inventory / SLO stubs | **SIM + DEV HTTP** | `fleet_ops.py` + diagnostics service | DEV reports persisted in shared store |
| Security telemetry (fleet) | **PARTIAL** | `fleet_ops` + `security_event_log` + OTEL redaction | Redaction helpers; not a SIEM |
| Cloud/edge modes LOCAL…CLOUD | **RUNNABLE DEV** | `cloud_edge/` + `cloud_dev_plane/` | Mode matrix on stubs **and** HTTP DEV plane |
| Identity / enrollment / sync / saves / matchmaking meta / telemetry / update metadata | **RUNNABLE DEV** | `deploy/cloud_dev_plane/` + `cloud_dev_plane/server.py` | Compose/containers or in-process HTTP |
| OpenTelemetry round-trip | **RUNNABLE DEV** | `otel_export.py` + collector config | `gunnchos.*` conventions + privacy redaction |
| Outage survival + resync | **RUNNABLE DEV** | `cloud_dev_plane/client.py` | Local outbox + `resync()` |
| DEV attestation | **EXISTS (DEV)** | `attestation.py` | No TPM / prod keys |
| DEV update signing | **EXISTS (DEV)** | `update_signing.py` | PROD realm rejected |
| SAST / abuse / SBOM / runbooks | **EXISTS (DEV)** | `security/dev_ops/`, `docs/security/INCIDENT_RUNBOOKS_DEV.md` | Not external pen-test |
| Threat model | **DOC (living)** | `docs/security/THREAT_MODEL.md` | Not external review |
| Adversarial / fuzz starters | **STARTER** | `tests/test_adversarial_fuzz_starters.py` | Not exhaustive fuzz campaign |
| Production MDM / carrier attach / NTN cert | **ABSENT** | — | External blockers |

Tokens: `DEV_*` only on the DEV plane; no production fleet, no carrier certification, no fictional named modem.
