# Lane H — exists vs stub (cloud / connectivity / fleet / security)

Honest inventory for FULL PRODUCT CONTINUATION III, Lane H.

| Surface | Status | Path | Notes |
| --- | --- | --- | --- |
| Radio capability profiles | **EXISTS (digital)** | `gunnchos_device_os/radio_capability.py` + device YAML `network:` | Profile-driven; rejects branded modem strings |
| Connectivity orchestrator | **EXISTS (digital)** | `gunnchos_device_os/connectivity_orchestrator.py` | Scores/handoff/faults; no live radio |
| Fleet enrollment / rings / canary / rollback | **SIM** | `gunnchos_device_os/fleet_ops.py` | In-process ops sim — not remote MDM |
| Health / diagnostics / inventory / SLO stubs | **SIM** | `fleet_ops.py` | SLO stubs optional `observe_slo` |
| Security telemetry (fleet) | **PARTIAL** | `fleet_ops.record_security_telemetry` + `security_event_log` | Redaction helpers; not a SIEM |
| Cloud/edge modes LOCAL…CLOUD | **STUB** | `gunnchos_device_os/cloud_edge/` | Mode capability matrix enforced in-process |
| Identity / enrollment / sync / saves / matchmaking meta / telemetry / update metadata | **STUB** | `cloud_edge/services.py` | Metadata & queues only |
| DEV attestation | **EXISTS (DEV)** | `attestation.py` | No TPM / prod keys |
| DEV update signing | **EXISTS (DEV)** | `update_signing.py` | PROD realm rejected |
| Threat model | **DOC (living)** | `docs/security/THREAT_MODEL.md` | Not external review |
| Adversarial / fuzz starters | **STARTER** | `tests/security/` | Not exhaustive fuzz campaign |
| Production MDM / carrier attach / NTN cert | **ABSENT** | — | External blockers |

Tokens: no production fleet, no carrier certification, no fictional named modem.
