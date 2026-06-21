# Hardware Release Signoff Template

**Status:** template only · **no signoffs recorded**

Copy for each hardware-compatible release milestone. Do not mark complete without linked evidence in [HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md](HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md).

---

## Release metadata

| Field | Value |
|-------|-------|
| Release name / version | |
| Target tier (R2 / R3) | |
| Date | |
| SKU(s) in scope | |
| OS repo git SHA | |
| Hardware repo git SHA | |

---

## Claim being signed

Check **one**:

- [ ] **R2 — Lab-validated compatibility** (reference hardware boot + DVT-linked OS tests)
- [ ] **R3 — Hardware-compatible product release** (DVT + cert + PVT + pilot)

**Not signable today:** All current hardware compatibility is simulated/profile-based unless evidence matrix rows are `validated`.

---

## Evidence attestation

| Area | Evidence link | Signer | Date | Pass |
|------|---------------|--------|------|:----:|
| Profile mirror audit | | | | ☐ |
| Simulated boot (CI) | | | | ☐ |
| Reference hardware boot | | | | ☐ |
| Display/input DVT | | | | ☐ |
| Battery DVT | | | | ☐ |
| Thermal DVT | | | | ☐ |
| Recovery / safe mode | | | | ☐ |
| HLK / drivers | | | | ☐ |
| Certification (FCC/CE/etc.) | | | | ☐ |
| PVT signoff | | | | ☐ |
| Field pilot | | | | ☐ |

Hardware repo evidence paths (when applicable):

- `../gunnchos-hardware-industrial-design/dvt/`
- `../gunnchos-hardware-industrial-design/pvt/`
- `../gunnchos-hardware-industrial-design/certification/`
- `../gunnchos-hardware-industrial-design/production_release/`

---

## Known gaps waived (if any)

| Gap ID | Description | Waiver rationale | Approver |
|--------|-------------|------------------|----------|
| | | | |

Empty unless explicit waivers with executive approval.

---

## Claim boundary acknowledgment

Signers acknowledge:

> This OS compatibility layer mirrors and validates hardware assumptions from the hardware repo. It does not prove physical hardware boot, HLK certification, driver certification, battery/thermal validation, or production hardware compatibility.

**unless** this signoff tier is R2/R3 **and** linked evidence explicitly covers the claimed scope.

---

## Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| OS engineering lead | | | |
| Hardware engineering lead | | | |
| QA lead | | | |
| Guardian/youth safety reviewer (if school/arena SKU) | | | |
| Executive sponsor (R3 only) | | | |

---

## Post-signoff actions

- [ ] Update [HARDWARE_COMPATIBILITY_STATUS.md](HARDWARE_COMPATIBILITY_STATUS.md)
- [ ] Update [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md) if scope expanded
- [ ] Update [../docs/HARDWARE_OS_TRACEABILITY.md](../docs/HARDWARE_OS_TRACEABILITY.md)
- [ ] Publish release notes with honest limitations

---

## Storage

Completed signoffs: `hardware_release/signoffs/YYYY-MM-DD_<release>.md` (future)
