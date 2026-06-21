# Build Artifacts Status

**Status:** `not_started` for release bundles · alpha source artifacts exist

---

## Build pipeline

| Component | Status | Notes |
|-----------|--------|-------|
| CI pytest + demos | **operational** | `.github/workflows/ci.yml` |
| Versioned OS-layer bundle build | **not_started** | No `dist/` release output |
| Signed manifest generation | **planned** | See SIGNING_REQUIREMENTS |
| Artifact upload to release storage | **not_started** | No release bucket configured |
| Reproducible build documentation | **planned** | RC backlog #2 |

---

## Current outputs (alpha)

| Output | Path | Release artifact? |
|--------|------|-------------------|
| Demo JSON | `results/` | No — evidence only |
| Python package source | repo root | No — not installable image |
| Launcher mock build | `apps/launcher_mock/` (npm dev) | No — not production bundle |

---

## Target RC build outputs

1. `gunnchos-os-layer-{version}-win-x64.bundle`
2. `manifest.json` (signed)
3. `checksums.sha256`
4. `sbom.spdx.json`
5. `recovery-{version}.bundle`
6. `RELEASE_NOTES.md`

**None of the above exist in the repository today.**

---

## Next steps

See [../roadmap/RELEASE_CANDIDATE_BACKLOG.md](../roadmap/RELEASE_CANDIDATE_BACKLOG.md) tasks #2–7.

---

## Claim boundary

Build artifact status is honest: release bundles are **not yet** produced. Alpha source is not a finished shipping OS image.
