# WP-007 Threat Model — Independent Security / Red-Team Readiness

**Status:** DRAFT digital threat model for Operating Cycle 2 WP-007  
**Evidence target:** E4 independent digital  
**External pentest:** E7 / `EXTERNAL_PENDING`  
**Claim boundary:** Internal digital readiness preparation only. Does **not** claim `production_ready` security, physical fault injection, carrier approval, or EXTERNAL pentest PASS.

Related:
- `docs/security/THREAT_MODEL.md` (prior living model)
- `docs/security/wp007/EXTERNAL_ASSESSMENT_PACKET.md`
- `docs/security/wp007/GOLDEN_JOURNEY_CONTROL_MAP.json`
- `gunnchos_device_os/security_red_team/harness.py`
- `artifacts/wp007/RED_TEAM_RESULTS.json`

---

## Method

STRIDE + privacy/AI-specific analysis per trust boundary. Each row records:
**asset · attacker · entry · privilege · abuse · mitigation · detection · recovery · test**.

Severity: **S0** catastrophe · **S1** core boundary bypass · **S2** serious w/ workaround · **S3/S4** backlog.

S0/S1 block `INTERNAL_RED_TEAM_READY`.

---

## Asset / trust-boundary inventory

| Boundary | Assets | Primary code |
| --- | --- | --- |
| Secure/verified boot | Boot evidence, DEV keys | `security/secure_boot`, `attestation.py` |
| OS image/update/rollback | Slot state, signatures, anti-rollback SV | `ota_state_machine.py`, `update_signing.py` |
| Recovery | Recovery hooks, wipe | boot/recovery stubs |
| Identity/session | Accounts, tokens, bindings, roles | `unified_identity.py`, `runtime/adapters.py` IdentityService |
| Secret abstraction | Per-user secrets | `stage2/security/sandbox.py` |
| Filesystem/encryption | Continuity vaults (dev XOR-HMAC) | `phase_xiv/continuity` |
| Package install/distribution | Signed packages, channels | `phase_xiv/packages`, `app_packaging.py` |
| Permissions/sandbox | Caps, IPC peers | `sandbox_policy.py`, PermissionsService |
| Developer mode | Role escalation | IdentityService `api_set_role` |
| MDM | Fleet revoke/wipe | `fleet_ops.py`, continuity wipe |
| gunnchAI memory/projects | Tutor prompts, project secrets | `gunnchai_integration.py`, sandbox secrets |
| AI tools/agents/computer use | Approval-gated actions | AiInterfaceService |
| Connectors/MCP/Skills | (digital stubs) | deferred E7 for live connectors |
| Scheduled tasks | (limited digital) | backlog S2 |
| Continuity | Clipboard/files/state/peripherals | `phase_xiv/continuity` |
| gunnchFabric | Discovery, trust, leases | `phase_xiv/fabric` |
| Rings/SpatialInput | Auth events, confidence | RingService, `ring_input/` |
| gunnchDevice Lab | Sessions, netns/uinput, manifests | `device_lab/` |
| Modem/network | Bearer selection | `connectivity_orchestrator.py` |
| Game online/social/save | Save integrity | ContinuityService saves; live game E7 |
| WAIKE/student data | Learning records | access-risk lab + privacy docs |
| Archive ingest | (limited) | backlog |
| Telemetry/support | Redacted events | `diagnostics_log` / security_event_log |
| Factory provisioning | DEV factory image | `os_build/`, factory |

---

## STRIDE matrix (digitally exercised)

| ID | Asset | Attacker | Entry | Privilege | Abuse | Mitigation | Detection | Recovery | Test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC-OS-001 | Session | Thief | Stolen token | User | Reuse after revoke | `revoke_session` → invalid | Audit revoke | Re-issue | harness |
| SEC-OS-002 | Session | Network peer | Token replay other device | User | Session fixation | device_id bind | `device_mismatch` | Re-auth | harness |
| SEC-OS-003 | Update | Malicious OTA | Lower SV package | System | Downgrade | anti-rollback SV | `anti_rollback_*` | Stay on slot | harness |
| SEC-OS-004 | Update | Supply chain | Bad signature | System | Tampered image | verify signature/digest | `signature_invalid` | Fail closed | harness |
| SEC-OS-005 | Roles | Local malware | `set_role` | Student/guest | Priv-esc to admin | break_glass gate | PermissionError | Keep role | harness |
| SEC-OS-006 | Packages | Malicious pkg | `../` app_id / channel down | Installer | Path escape / downgrade | sanitize + channel deny | Value/PermissionError | Refuse install | harness |
| SEC-OS-007 | Sandbox | Confused app | SYSTEM_SERVICE / cross secret | Untrusted | Escape / exfil | default deny + caller_id | denials audit | Revoke caps | harness |
| SEC-AI-001 | AI tools | Prompt attacker | Injected prompt | AI session | Tool/exfil / CU bypass | injection guard + approval | deny reasons | Drop turn | harness |
| SEC-AI-002 | AI memory | Sibling project | Cross secret get | Project B | Cross-project leak | caller_id isolation | PermissionError | Namespace | harness |
| SEC-RING-001 | Ring input | Lost/forged ring | Unauth events | Input | HID inject / retarget | auth + confidence | fallback | Pair+auth | harness |
| SEC-FABRIC-001 | Fabric | Impersonator | Unilateral trust | Node | Lease steal | mutual enrollment tokens | denials log | Re-enroll | harness |
| SEC-FABRIC-002 | Continuity | Impersonator | Guessed device secret | Peer | Clipboard exfil | random secrets + wipe deny | PermissionError | Wipe+revoke | harness |
| SEC-NET-001 | Network | Evil twin | Hostile Wi-Fi metrics | Connectivity | Prefer open Wi-Fi | security_score | score compare | Prefer ethernet | harness (S2) |
| SEC-GAME-001 | Game save | Cheater | Tampered save | Local | Score inflate | integrity digest | mismatch | Reject | harness (S2) |
| SEC-LAB-001 | Device Lab | Local user | `work=../` | Lab CLI | Host escape | path containment | PermissionError | Refuse start | harness |

---

## Privacy / AI-specific

| Threat | Mitigation (digital) | Residual |
| --- | --- | --- |
| Prompt injection | `tutor_prompt_guard` / AiInterface markers | Model-level eval E7 |
| Indirect injection via docs | Local-only privacy mode | Connector sandbox E7 |
| Memory poisoning | Project secret isolation | Durable vector store ACL E7 |
| Citation / attribution error | Provenance stub fields | Scientific eval E7 |
| Student PII in telemetry | Redaction helpers / consent | Full DLP E7 |
| Youth safety | Role + guardian docs | Human review EXTERNAL |

---

## Golden Journey safety mapping

See `GOLDEN_JOURNEY_CONTROL_MAP.json`. Critical:

| Journey | Security controls |
| --- | --- |
| GOLDEN-07 Ring | SEC-RING-001 auth/confidence |
| GOLDEN-08 Private AI | SEC-AI-001/002 privacy + injection |
| GOLDEN-09 Update rollback | SEC-OS-003/004 |
| GOLDEN-10 Lost device revoke | SEC-OS-001 + continuity wipe SEC-FABRIC-002 |
| GOLDEN-03 Package install | SEC-OS-006/007 |

---

## Explicit non-claims

- No production secure boot keys / HSM / TPM quotes
- No EXTERNAL penetration test execution
- No physical Ring / modem / carrier attach
- No frontier OS parity
- `PHYSICAL_EXECUTION_FREEZE` honored
