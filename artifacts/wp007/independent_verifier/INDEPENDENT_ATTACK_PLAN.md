# VP-007R Independent Attack Plan (Cycle 2 — derived BEFORE treating implementer PREPARED as PASS)

Sources (refreshed for accepted main `3908de7` / tip `7e5ab2f`):
- VP-007 / VP-007R Independent Verifier Packet
- WP-007 / WP-007R asset/boundary inventory + residual digital S2 targets
- Architecture: `unified_identity`, `PackageManager`, `SandboxEnforcer`,
  `GunnchFabric`, `ContinuityMesh`, `RingService`, `AiInterfaceService`,
  Device Lab session allowlist, `OtaStateMachine` / `UpdaterService` +
  `security.wp007.update_trust`, hostile-network digital simulator,
  `game_save_integrity` HMAC store
- Golden Journey safety paths GOLDEN-03/07/08/09/10
- Prior Independent FAIL (#92) + SEC-LAB CI fix (#93) — history preserved

Implementer `CLOSED_DIGITAL_PREPARED` / `E4_PREPARED` is **not** an oracle.
Independent PASS requires re-derivation + live attack execution on accepted main.

## Attack axes (independent case IDs)

| ID | Boundary | Attack |
| --- | --- | --- |
| IV-OS-001 | identity | revoked session still validates |
| IV-OS-002 | identity | token reused on wrong device |
| IV-OS-003 | package | unsigned / tampered payload install |
| IV-OS-004 | package | stable→dev channel downgrade |
| IV-OS-005 | package | revoked app reinstall |
| IV-OS-006 | package | path-escape app_id (`../`) |
| IV-OS-007 | sandbox | cross-user secret_get |
| IV-OS-008 | sandbox | path-escape user_id |
| IV-OS-009 | update | bad-update → rollback; user data preserved |
| IV-OS-010 | update | OTA verify rejects signature_valid=False |
| IV-OS-011 | update | UpdaterService Ed25519 happy-path verify |
| IV-OS-012 | update | wrong key / tampered payload / metadata / missing / malformed / rollback / force_verified |
| IV-OS-013 | update | PRODUCTION_TRUST_ROOT realm EXTERNAL_PENDING |
| IV-AI-001 | AI | prompt/tool injection into tutor_prompt_guard |
| IV-AI-002 | AI | computer_use without approval_token |
| IV-AI-003 | AI | unsafe response patterns not flagged |
| IV-RING-001 | Ring | unauthenticated event injection |
| IV-RING-002 | Ring | low-confidence destructive gesture |
| IV-RING-003 | Ring | unauth set_target_device |
| IV-RING-004 | Ring | non-DEV auth token |
| IV-FAB-001 | Fabric | trust without enrollment tokens |
| IV-FAB-002 | Fabric | lease from untrusted consumer |
| IV-FAB-003 | Fabric | bad enrollment token |
| IV-CONT-001 | Continuity | handoff after wipe |
| IV-CONT-002 | Continuity | cross-user handoff |
| IV-CONT-003 | Continuity | HMAC integrity tamper on unseal |
| IV-LAB-001 | Device Lab | unapproved work path escape denied |
| IV-LAB-002 | Device Lab | unregistered temp denied |
| IV-LAB-003 | Device Lab | host-sensitive root not approvable |
| IV-LAB-004 | Device Lab | registered controlled root allowed; escape still denied |
| IV-LAB-005 | Device Lab | default instances root allowed |
| IV-NET-001 | Network | fleet command after revoke |
| IV-NET-002 | Network | hostile DNS/TLS/captive/downgrade; no credential leak |
| IV-GAME-001 | Game | unauthenticated digest rejected; HMAC tamper quarantine |
| IV-GAME-002 | Game | cross-device binding mismatch |

Expected safe result for all digital cases: deny / rollback / preserve / no delivery.
S0/S1 observed → file defect; blocks INTERNAL_RED_TEAM_READY.

## Residual targets (Independent verdict only)

| Residual | Independent target if earned |
| --- | --- |
| WP007-IV-RES-001 | CLOSED_DIGITAL (DEV_TEST Ed25519; PRODUCTION EXTERNAL_PENDING) |
| WP007-IV-RES-002 digital | HOSTILE_NETWORK_DIGITAL=E4_PASS; RF E5/E8 EXTERNAL_PENDING |
| WP007-IV-RES-003 digital | LOCAL_SAVE_INTEGRITY_DIGITAL=E4_PASS; AUTHORITATIVE_MULTIPLAYER EXTERNAL_PENDING |

External pentest / physical FI / carrier / production HSM ceremony = EXTERNAL_PENDING (not claimed).
