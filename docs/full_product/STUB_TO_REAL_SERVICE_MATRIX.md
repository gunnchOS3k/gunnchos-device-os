# Image service stub → real matrix (Continuation V)

| # | Service | Stub (#61) | Real (V) | Startup | Health | Shutdown | Restart | Logs | Persistence | IPC |
|---|---------|------------|----------|---------|--------|----------|---------|------|-------------|-----|
| 1 | hal | PID write + exit | long-lived daemon | yes | GET /health | POST /shutdown | yes | `/var/log/gunnchos/hal.log` | state file | mailbox HTTP-line |
| 2 | input | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 3 | ring | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 4 | display | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 5 | dock | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 6 | continuity | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 7 | identity | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 8 | permissions | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 9 | sandbox | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 10 | connectivity | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 11 | ai_interface | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 12 | profile_manager | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 13 | a11y | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 14 | diagnostics | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 15 | updater | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 16 | recovery | stub | daemon | yes | yes | yes | yes | yes | yes | yes |
| 17 | fleet_agent | stub | daemon | yes | yes | yes | yes | yes | yes | yes |

**Host IPC plane (Python):** AF_UNIX JSON-line + local HTTP (`IpcRuntimePlane`) — proves cross-process service calls outside the guest.

**Not earned:** `FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE` (guest transport is mailbox HTTP-line inside busybox minirootfs; no production gRPC mesh).
