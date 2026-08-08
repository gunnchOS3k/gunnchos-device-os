# FULL PRODUCT CONTINUATION V — stub elimination + real IPC + cloud persistence

## Scope

Continuation from merged #61 (bootable QEMU reference image) + #60 (runnable cloud/fleet DEV plane).

This wave converts image **service stubs** into **supervised real services**, adds **real local IPC**, proves QEMU boot with cross-service calls + first-party manifests, and upgrades the cloud DEV plane to **SQLite persistence** with multi-instance/failure tests.

## Honest tokens

| Token | Meaning |
|-------|---------|
| `GUNNCHOS_BOOTABLE_REFERENCE_IMAGE_DIGITAL_PASS` | QEMU serial boot evidence still earned (narrow-valid OK) |
| `GUNNCHOS_RUNTIME_IPC_DIGITAL_PASS` | Host Unix-socket / local-HTTP IPC cross-service calls pass |
| `GUNNCHOS_PHYSICAL_BOOT_PENDING` | Always co-emitted — no physical device boot claim |
| `FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE` | **Forbidden / not earned** — guest IPC is mailbox HTTP-line (not full AF_UNIX/gRPC mesh), cloud is DEV-only |

**Not claimed:** production keys, physical boot, MDM, carrier networking, FULL_OPERATIONAL_PRODUCT.

## Stub → real matrix (image services)

| Service | Before (#61) | After (V) | Lifecycle | IPC | Persistence |
|---------|--------------|-----------|-----------|-----|-------------|
| hal | PID-only stub | supervised daemon | start/stop/restart/health/logs | mailbox HTTP-line | `/var/lib/gunnchos/state/hal.state` |
| input | stub | supervised daemon | same | same | yes |
| ring | stub | supervised daemon | same | same | yes |
| display | stub | supervised daemon | same | same | yes |
| dock | stub | supervised daemon | same | same | yes |
| continuity | stub | supervised daemon | same | same | yes |
| identity | stub | supervised daemon | same | same | yes |
| permissions | stub | supervised daemon | same | same | yes |
| sandbox | stub | supervised daemon | same | same | yes |
| connectivity | stub | supervised daemon | same | same | yes |
| ai_interface | stub | supervised daemon | same | same | yes |
| profile_manager | stub | supervised daemon | same | same | yes |
| a11y | stub | supervised daemon | same | same | yes |
| diagnostics | stub | supervised daemon | same | same | yes |
| updater | stub | supervised daemon | same | same | yes |
| recovery | stub | supervised daemon | same | same | yes |
| fleet_agent | stub | supervised daemon | same | same | yes |

Host digital runtime adds **AF_UNIX + local HTTP** IPC (`gunnchos_device_os/runtime/ipc.py`) — not in-process-only integration.

## QEMU proof markers (added)

- `GUNNCHOS_SERVICES_KIND=supervised_real`
- `GUNNCHOS_IPC=ok` / `GUNNCHOS_IPC_CROSS_CALL=true`
- `GUNNCHOS_APP_MANIFEST=ok` / `GUNNCHOS_GAME_MANIFEST=ok`
- `FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE=false`

## Cloud DEV plane persistence (#60 follow-on)

| Backend | When |
|---------|------|
| `sqlite` (default for compose) | `GUNNCHOS_STORE_PATH=*.sqlite3` or `GUNNCHOS_STORE_BACKEND=sqlite` |
| `json` | explicit `*.json` path |
| `memory` | no path (unit tests) |
| Redis (optional) | `GUNNCHOS_REDIS_URL` / `REDIS_URL` — coordination only |

Multi-instance: WAL + merge-on-write; failure tests stop one gateway while the peer continues.

## Commands

```bash
PYTHONPATH=.:src pytest -q \
  tests/test_bootable_reference_image.py \
  tests/test_runtime_ipc.py \
  tests/test_cloud_dev_plane_persistence.py \
  tests/test_cloud_dev_plane_modes.py \
  tests/test_cloud_dev_plane_outage_resync.py

make full-product-v
```
