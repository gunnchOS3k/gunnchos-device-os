# Threat model — school fleet, OTA, cloud/edge, measurement

**Status:** Living research threat model (digital). **Not** a formal security assessment or production pen-test report.

**Claim boundary:** Documents intended threats and mitigations for the gunnchOS research prototype. Does not claim SOC2, Common Criteria, carrier certification, or production MDM hardening.

## Scope

| In scope (digital / sim) | Out of scope (honest gaps) |
| --- | --- |
| Local policy agent & enrollment sim | Remote production MDM |
| DEV-realm attestation & update signing | Production code-signing / HSM / TPM quotes |
| Connectivity orchestrator decisions | Live modem / SIM / carrier attach |
| Cloud/edge stubs (LOCAL…CLOUD modes) | Deployed campus or public cloud |
| Fleet rings / canary / rollback sim | Real staged rollout to hardware fleets |
| Security event redaction helpers | Full SIEM / SOC operations |

## Assets

1. Student / guardian identity records (local & stub sync)
2. Device inventory and enrollment tokens (sim)
3. OTA package manifests and signatures (DEV realm)
4. Measurable-boot evidence documents (DEV realm)
5. Telemetry and diagnostics logs (redacted)
6. Offline save / sync queues
7. Matchmaking *metadata* (not live game traffic)

## Actors

| Actor | Intent |
| --- | --- |
| Student / end user | Normal use; may probe local APIs |
| Guardian / teacher | Policy changes within role |
| Fleet admin | Enrollment, rings, rollback |
| Compromised device | Forge attestation, skip update verify |
| Network adversary | MITM on campus/cloud stubs, inject telemetry |
| Malicious update author | Ship unsigned / wrong-realm packages |
| Curious researcher | Fuzz local stubs and orchestrator |

## Threats & mitigations (current digital depth)

| ID | Threat | Impact | Current mitigation | Residual |
| --- | --- | --- | --- | --- |
| T-01 | Forged measurable-boot evidence | Trust false boot state | DEV HMAC verify; PROD realm rejected | DEV secret is in-repo — not production trust |
| T-02 | Unsigned / tampered update package | Bad software installed | `update_signing` DEV verify; OTA sim rejects bad signature fault | No production cert chain |
| T-03 | Enrollment of unauthorized device | Fleet pollution | Enrollment sim + revoke path | No remote authority |
| T-04 | Canary failure ignored → broad blast | Fleet regression | Canary abort threshold → rollback | Sim only |
| T-05 | Guest reads fleet telemetry | Privacy leak | Access-risk notes; redaction in security_event_log | Not enforced across all UIs |
| T-06 | Open Wi-Fi preferred over trusted ethernet | Integrity / privacy | Orchestrator security_score + profile constraints | Injected metrics only |
| T-07 | NTN / cellular path treated as certified | False certification claim | Capability classes `simulated_*`; claim_boundary on snapshots | Docs/tests must keep honest tokens |
| T-08 | DISCONNECTED mode still syncs to cloud | Data exfil / policy break | Mode capability matrix denies sync/telemetry | Stub-level only |
| T-09 | Adversarial input to orchestrator / parsers | Crash / bad handoff | Fuzz starters in `tests/test_adversarial_fuzz_starters.py` | Coverage starter, not exhaustive |
| T-10 | Measurement-mode data mixed into school telemetry | Sensitive research leak | Separate event types; consent docs | Incomplete enforcement |

## Trust boundaries

```
[Device local] --policy--> [Fleet ops sim]
[Device local] --DEV sign--> [Update metadata stub]
[Device local] --mode--> [CloudEdgeFabric: LOCAL|DISCONNECTED|CAMPUS_EDGE|CLOUD]
[Radio capability profile] --constraints--> [ConnectivityOrchestrator]
```

No boundary may be labeled production-trusted without external keys and hardware evidence.

## Review checklist (open)

- [ ] External security review of threat model
- [ ] Production signing root ceremony (blocked: no HSM / keys)
- [ ] TPM / measured boot on reference hardware
- [ ] Remote MDM threat model when server exists
- [ ] Carrier / NTN partner security questionnaire (blocked: partners)

## Related evidence

- `gunnchos_device_os/attestation.py` — DEV measurable-boot
- `gunnchos_device_os/update_signing.py` — DEV update signing
- `gunnchos_device_os/fleet_ops.py` — fleet sim
- `gunnchos_device_os/cloud_edge/` — mode-aware stubs
- `gunnchos_device_os/connectivity_orchestrator.py` + `radio_capability.py`
- `tests/test_adversarial_fuzz_starters.py` — adversarial / fuzz starters
- `docs/LANE_H_EXISTS_VS_STUB.md` — honest inventory
