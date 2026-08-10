# VP-007 Independent Attack Plan (derived BEFORE treating implementer corpus as oracle)

Sources: VP-007, WP-007 asset/boundary inventory, architecture modules
(`unified_identity`, `PackageManager`, `SandboxEnforcer`, `GunnchFabric`,
`ContinuityMesh`, `RingService`, `AiInterfaceService`, Device Lab session,
`UpdateManager` / OTA adapters), Golden Journey safety paths GOLDEN-07/09/10.

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
| IV-OS-010 | update | UpdaterService verify/stage without real signature check |
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
| IV-LAB-001 | Device Lab | work path escape outside instances root |
| IV-NET-001 | Network | fleet command after revoke |
| IV-GAME-001 | Game | save payload digest mismatch rejection |

Expected safe result for all digital cases: deny / rollback / preserve / no delivery.
S0/S1 observed → file defect; blocks INTERNAL_RED_TEAM_READY.
External pentest / physical FI / carrier = EXTERNAL_PENDING (not claimed).
