# Hardware Release Compatibility

**Status:** All current hardware compatibility is simulated/profile-based. Real hardware validation is required before hardware-compatible release can be claimed.

Documentation for hardware-compatible **release gates**, evidence, testing, and signoff.

**Hardware repo:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Documents

| Document | Purpose |
|----------|---------|
| [HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md](HARDWARE_COMPATIBILITY_RELEASE_REQUIREMENTS.md) | Release requirements |
| [HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md](HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md) | Evidence by device class |
| [HARDWARE_COMPATIBILITY_TEST_PLAN.md](HARDWARE_COMPATIBILITY_TEST_PLAN.md) | Test plan |
| [HARDWARE_COMPATIBILITY_STATUS.md](HARDWARE_COMPATIBILITY_STATUS.md) | Current status |
| [HARDWARE_VALIDATION_LAB_CHECKLIST.md](HARDWARE_VALIDATION_LAB_CHECKLIST.md) | Lab checklist |
| [HARDWARE_PILOT_TEST_PLAN.md](HARDWARE_PILOT_TEST_PLAN.md) | Field pilot plan |
| [HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md](HARDWARE_RELEASE_SIGNOFF_TEMPLATE.md) | Signoff template |

---

## Release claim rule

A hardware-compatible release may **not** be claimed until:

1. Evidence matrix rows reach `validated` with linked artifacts
2. Hardware repo DVT/PVT/cert gates align with OS evidence
3. Signoff template completed by engineering owners
4. Claim boundary document updated to reflect **only** proven scope

---

## Related OS packages

- `hardware_compat/` — profiles and contract
- `boot_readiness/` — boot simulation and T1 requirements
- `release_gates/` — general OS release gates
- `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md`

---

## Hardware repo release alignment

| Hardware gate | Hardware path |
|---------------|---------------|
| DVT | `dvt/DVT_STATUS.md` |
| PVT | `pvt/PVT_STATUS.md` |
| Certification | `certification/CERTIFICATION_STATUS.md` |
| Production release | `production_release/PRODUCTION_RELEASE_STATUS.md` |

All hardware gates: **not complete / not certified / not released** as of this pass.
