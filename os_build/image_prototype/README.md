# GunnchOS Image Prototype Track

**Status:** OS-layer packaging track — **not** a bootable production OS image.

## Artifact types (honest labels)

| Type | Status | Path |
|------|--------|------|
| OS-layer package | Planned | Python wheel + launcher bundle |
| Container kiosk prototype | **This track** | `os_build/image_prototype/` |
| VM image | Not built | — |
| Installable OS image (x86_64) | Not built | — |
| Hardware boot on target SKU | Not validated | — |

## x86_64 strategy (first)

1. Package launcher + policy into container kiosk artifact
2. Simulate first boot → kiosk launcher → health check
3. Document path to VM/raw image without claiming completion

## Build

```bash
bash os_build/image_prototype/build_kiosk_package.sh
bash os_build/image_prototype/healthcheck.sh
bash scripts/generate_artifact_checksums.sh
```

## Docker (optional)

```bash
cd os_build/image_prototype
docker build -t gunnchos-kiosk-prototype .
docker run --rm -p 8080:80 gunnchos-kiosk-prototype
curl -f http://localhost:8080/health
```
