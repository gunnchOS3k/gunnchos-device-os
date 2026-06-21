# SBOM Requirements

**Status:** requirement defined · SBOM **not yet** generated for releases

---

## Purpose

Software Bill of Materials (SBOM) for each RC+ release enables dependency review, vulnerability tracking, and supply-chain audit.

---

## Format

- **Preferred:** SPDX 2.3 JSON (`sbom.spdx.json`)
- **Acceptable:** CycloneDX 1.5 JSON
- Must list: Python dependencies, npm dependencies (launcher), bundled configs, third-party assets

---

## Scope

| Component | Include |
|-----------|---------|
| `requirements.txt` / pip lock | Yes |
| `apps/launcher_mock/package-lock.json` | Yes |
| Vendored assets | Yes |
| Windows/OS dependencies | Document as external where not bundled |

---

## Generation

- Automated in CI on release tag
- Stored alongside release bundle
- Hash listed in version manifest

**Current status:** SBOM has **not** been signed and published — placeholder pipeline only (RC backlog #5).

---

## Review process

1. Generate SBOM in CI
2. Security review diff vs previous release
3. Block release on critical unmitigated CVEs (policy TBD)
4. Archive SBOM per [ARTIFACT_MANIFEST_REQUIRED.md](ARTIFACT_MANIFEST_REQUIRED.md)

---

## Claim boundary

SBOM **requirement** is defined. The repo does **not** claim sbom has been signed and published for any release until artifact exists in manifest.
