# Digital container / VM packet — not a shipping OS

**Status:** prototype sources + checksums. `GUNNCHOS_PHYSICAL_SYSTEM_IMAGE_PENDING` remains.

## What exists

| Artifact | Role | Claim |
|---|---|---|
| `os_build/linux_desktop/docker-compose.yml` | nginx + launcher_mock dist on :8080 | Container **prototype** |
| `.devcontainer/devcontainer.json` | Python 3.11 + Node 20 devcontainer | Developer environment |
| `os_build/reproducible_system_image/artifacts/CHECKSUMS.json` | Deterministic DEV factory **bundle** hashes | Digital path; `bootable=false` |
| `make bootable-reference` | QEMU aarch64/x86 DEV/VM harness | Not physical boot |

## Checksums

Regenerate:

```bash
PYTHONPATH=.:src python3 scripts/checksum_digital_container_vm.py
```

Output: `artifacts/supervisor_ready/DIGITAL_CONTAINER_VM_CHECKSUMS.json`.

Do not treat Docker :8080 or the DEV factory JSON bundle as an installable
consumer OS image.
