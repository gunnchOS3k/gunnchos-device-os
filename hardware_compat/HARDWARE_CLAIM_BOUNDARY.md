# Hardware Claim Boundary

**Status:** enforced in profiles and engine · **do not overclaim**

---

## Authoritative boundary text

This OS compatibility layer mirrors and validates hardware assumptions from the hardware repo. It does not prove physical hardware boot, HLK certification, driver certification, battery/thermal validation, or production hardware compatibility.

---

## Allowed claims today

| Claim | Basis |
|-------|-------|
| Device profile loaded for SKU X | YAML profile + manifest loader |
| Mode Y is supported / blocked for SKU X per profile | Compatibility engine + policy modules |
| Simulated boot readiness check passed | `hardware_boot_readiness.py` with `status: simulated` |
| Hardware repo source paths cited in profile | `hardware_repo_source_paths` in YAML |
| Documentation aligned with hardware repo planning artifacts | Audit and traceability docs |

---

## Disallowed claims today

| Claim | Why not |
|-------|---------|
| gunnchOS boots on reference hardware for SKU X | No hardware boot logs linked |
| Hardware-compatible release | All validation simulated/profile-based |
| HLK or driver certification complete | Not run |
| School-day battery life validated | No DVT battery reports |
| Thermal throttle validated under load | No DVT thermal reports |
| FCC/CE/UKCA certified product | `certification/CERTIFICATION_STATUS.md`: not certified |
| DVT or PVT complete | Hardware status docs: not complete |
| Production hardware released | `production_release/PRODUCTION_RELEASE_STATUS.md`: not released |
| Steam compatibility certified (Handheld) | Known gap in profile |
| Arena safety field-validated (Wearables) | Known gap in profile |

---

## Evidence tags

The compatibility engine attaches `real_hardware_validation_required` to evaluation results. Treat this tag as a **blocker for external hardware-compatible release messaging**.

---

## Profile-level boundary

Every file under `device_profiles/` includes:

```yaml
claim_boundary: Profile mirror — not physical hardware validation
```

Do not remove or soften this field without linked lab evidence and release signoff.

---

## Hardware repo claim boundary

Mirror and respect:

- `../gunnchos-hardware-industrial-design/product/CLAIM_BOUNDARY.md`
- `../gunnchos-hardware-industrial-design/mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md`
- `../gunnchos-hardware-industrial-design/dvt/DVT_STATUS.md`
- `../gunnchos-hardware-industrial-design/certification/CERTIFICATION_STATUS.md`

---

## Release messaging rule

Before any public statement that gunnchOS is "hardware compatible" or "validated on device X":

1. Row in `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` must show `validated` with linked artifact.
2. `hardware_release/HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md` must be completed.
3. This document must be updated to narrow — not expand — the disallow list based on new evidence only.

---

## Related documents

- [HARDWARE_VALIDATION_STATUS.md](HARDWARE_VALIDATION_STATUS.md)
- [../hardware_release/HARDWARE_COMPATIBILITY_STATUS.md](../hardware_release/HARDWARE_COMPATIBILITY_STATUS.md)
- [../docs/HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md](../docs/HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md)
