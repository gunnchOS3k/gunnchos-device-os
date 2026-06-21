# Release Artifacts

**Status:** artifact model documented · **most RC artifacts not yet built**

Defines what must exist at each release stage. See [ARTIFACT_MANIFEST_REQUIRED.md](ARTIFACT_MANIFEST_REQUIRED.md) for the full manifest.

## Documents

| Document | Purpose |
|----------|---------|
| [ARTIFACT_MANIFEST_REQUIRED.md](ARTIFACT_MANIFEST_REQUIRED.md) | Alpha vs RC-required artifacts |
| [BUILD_ARTIFACTS_STATUS.md](BUILD_ARTIFACTS_STATUS.md) | Build pipeline status |
| [INSTALLER_STATUS.md](INSTALLER_STATUS.md) | Installer status |
| [IMAGE_STATUS.md](IMAGE_STATUS.md) | OS image/layer status |
| [CHECKSUMS_STATUS.md](CHECKSUMS_STATUS.md) | Checksum pipeline status |
| [SBOM_REQUIREMENTS.md](SBOM_REQUIREMENTS.md) | SBOM requirements |
| [SIGNING_REQUIREMENTS.md](SIGNING_REQUIREMENTS.md) | Signing requirements |
| [RECOVERY_ARTIFACT_REQUIREMENTS.md](RECOVERY_ARTIFACT_REQUIREMENTS.md) | Recovery bundle requirements |
| [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md) | Release notes template |
| [VERSION_MANIFEST_TEMPLATE.json](VERSION_MANIFEST_TEMPLATE.json) | Version manifest JSON template |

## Validation

```bash
python scripts/validate_release_artifacts.py
```

## Claim boundary

Artifact docs describe required and current status. They do **not** claim installer is available for download or that installable image has been validated on hardware unless status explicitly says so with evidence link.
