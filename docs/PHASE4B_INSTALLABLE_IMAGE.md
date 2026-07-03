# GunnchOS Phase 4B — Installable OS Image Track

**Branch:** `phase4b-installable-os-image`  
**Issues:** OS-001 (installable artifact path)

## Real after this PR

- `os_build/installable_image/` — installable image prototype track
- `scripts/build_installable_image.sh` — builds tarball bundle + manifest + checksums
- `scripts/validate_installable_image_artifacts.py` — structural + honesty validation
- `hardware_validation/BOOT_VALIDATION_TEMPLATE.md` — boot evidence gate
- Updated `release_artifacts/version_manifest.example.json` — `installable_os_image: prototype`
- `tests/test_installable_image.py` — CI smoke

## Artifact level achieved

**Prototype (OS-layer bundle)** — reproducible `.tar.gz` with launcher, policy, install stubs, `MANIFEST.json`, and `CHECKSUMS.sha256`.

Not achieved:

- Bootable ISO/IMG
- Hardware boot validation
- Signed production installer

## Explicitly NOT claimed

- Bootable OS on target hardware
- GA / beta release
- ISO/IMG suitable for USB flash or bare-metal install
- Secure boot / TPM validation

## Validation

```bash
bash scripts/build_installable_image.sh
bash os_build/installable_image/healthcheck.sh
python3 scripts/validate_installable_image_artifacts.py
pytest tests/test_installable_image.py -q
make validate-full
```

## Path to validated bootable image

1. Produce real ISO/IMG via Yocto or image builder
2. Complete `hardware_validation/BOOT_VALIDATION_TEMPLATE.md`
3. Update `MANIFEST.json` fields only with linked evidence
4. Advance `beta_gate/beta_gate_status.yaml` `bootable_image` from `prototype` → `validated`
