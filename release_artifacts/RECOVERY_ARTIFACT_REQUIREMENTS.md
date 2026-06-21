# Recovery Artifact Requirements

**Status:** requirements defined · recovery bundle **not built**

---

## Purpose

Offline recovery when OS-layer fails to boot, update fails, or admin requires factory reset.

---

## Recovery bundle contents

| File | Purpose |
|------|---------|
| `recovery-manifest.json` | Signed file list |
| `recovery-launcher/` | Minimal launcher shell |
| `policy-safe-defaults/` | Fallback YAML bundle |
| `reset-scripts/` | Profile wipe / factory reset |
| `README-RECOVERY.txt` | Human instructions |

---

## Functional requirements

1. Bootable from USB on supported SKUs (when hardware program defines path)
2. Verify signature before apply
3. Offer: last known good, rollback version, factory reset
4. Preserve user data option where policy allows
5. Guardian/school rules enforced (PIN, admin auth)

See [../requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md](../requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md).

---

## Build and release

- Versioned with OS-layer semver
- Checksum published in release manifest
- Tested in RC gate: recovery drill log required

---

## Alpha today

- Recovery behavior documented only
- `rollback.py` design — not recovery bundle artifact

---

## RC backlog

Task #8: Add rollback/recovery demo with logged output.

---

## Claim boundary

Recovery artifact **requirements** are specified. No recovery bundle exists in the repository today.
