# GunnchOS Phase 2F — Bootable Image Prototype Track

**Branch:** `phase2f-bootable-image-prototype-track`  
**Issues:** OS-001

## Real after this PR

- Documented x86_64 packaging strategy under `os_build/image_prototype/`
- `build_kiosk_package.sh` — packages launcher + policy into artifact dir
- `healthcheck.sh` — smoke validation
- `ARTIFACT_MANIFEST.md` + checksum script
- `release_artifacts/version_manifest.example.json`

## Explicitly NOT claimed

- Bootable OS on target hardware
- GA / beta release
- VM/raw disk image (documented path only)

## Validation

```bash
bash os_build/image_prototype/build_kiosk_package.sh
bash os_build/image_prototype/healthcheck.sh
pytest tests/test_image_prototype.py -q
make validate-full
```
