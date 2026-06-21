# Signing Requirements

**Status:** plan documented · production signing **not operational**

---

## Purpose

Cryptographic signing ensures update and install integrity. Required before RC gate.

---

## Objects to sign

| Object | Algorithm (target) | Status |
|--------|-------------------|--------|
| Release manifest (`manifest.json`) | Ed25519 or RSA-4096 | planned |
| OS-layer bundle | Manifest covers file hashes | planned |
| Recovery bundle | Same key hierarchy | planned |
| Update package | Channel-specific key | planned |
| SBOM | Optional co-signature | planned |

---

## Key tiers

| Tier | Use | Storage |
|------|-----|---------|
| Dev | Local/CI unsigned or dev-signed builds | CI secret (dev) |
| RC | Release candidate builds | HSM or restricted vault |
| GA | Public release | HSM + ceremony doc |
| Revocation | Compromised key | Published revocation list |

---

## Verification

- Installer rejects unsigned or tampered manifests
- Updater verifies signature before apply
- Rollback bundles signed with same or previous key per policy

---

## Placeholder (RC backlog #7)

Signed update manifest **placeholder** in build pipeline — structure only, dev key — until key ceremony complete.

---

## Claim boundary

Signing **requirements** are defined. The repo does **not** claim complete secure boot on all devices or that production signing pipeline is operational.
