# Hardware Validation Lab Checklist

**Status:** checklist ready · **lab sessions not executed**

Use before and during P1/P2 hardware compatibility testing. Hardware repo lab RFQs: `../gunnchos-hardware-industrial-design/vendor_labs/`

---

## Pre-session setup

| # | Item | Done |
|---|------|:----:|
| 1 | Reference unit identified (SKU, serial, build) | ☐ |
| 2 | OS image version recorded | ☐ |
| 3 | Profile YAML version / git SHA recorded | ☐ |
| 4 | Hardware repo DVT plan printed for SKU | ☐ |
| 5 | Evidence matrix row IDs assigned | ☐ |
| 6 | Log capture path created (`results/hardware_boot/`) | ☐ |
| 7 | USB recovery media prepared | ☐ |
| 8 | Thermal chamber / load tools (if P2) | ☐ |
| 9 | Battery cycler / runtime script (if P2) | ☐ |
| 10 | Guardian test account configured | ☐ |

---

## Instrumentation

| # | Item | Done |
|---|------|:----:|
| 11 | Serial console attached | ☐ |
| 12 | Display photo/video capture | ☐ |
| 13 | Power meter (battery tests) | ☐ |
| 14 | Thermal camera or probes | ☐ |
| 15 | Controller test jig (Handheld) | ☐ |
| 16 | Dock / DP monitor (Student, Handheld, DS-XL) | ☐ |
| 17 | Network isolation for offline tests | ☐ |

---

## Per-SKU quick checks (P1)

### Student 14.5

| # | Check | Pass | Fail | N/A |
|---|-------|:----:|:----:|:---:|
| S1 | Cold boot to shell | ☐ | ☐ | ☐ |
| S2 | 1920×1200 internal panel | ☐ | ☐ | ☐ |
| S3 | Keyboard + touch + stylus | ☐ | ☐ | ☐ |
| S4 | Dock external display | ☐ | ☐ | ☐ |
| S5 | School mode launch | ☐ | ☐ | ☐ |
| S6 | Simulated vs actual profile match | ☐ | ☐ | ☐ |

### Handheld Hybrid

| # | Check | Pass | Fail | N/A |
|---|-------|:----:|:----:|:---:|
| H1 | Cold boot with controller | ☐ | ☐ | ☐ |
| H2 | Controller all buttons mapped | ☐ | ☐ | ☐ |
| H3 | TV/dock display | ☐ | ☐ | ☐ |
| H4 | Play mode thermal snapshot | ☐ | ☐ | ☐ |
| H5 | Battery runtime spot check | ☐ | ☐ | ☐ |

### DS-XL Coder

| # | Check | Pass | Fail | N/A |
|---|-------|:----:|:----:|:---:|
| D1 | Dual-screen detected | ☐ | ☐ | ☐ |
| D2 | Dual-touch functional | ☐ | ☐ | ☐ |
| D3 | Deploy to Student target | ☐ | ☐ | ☐ |
| D4 | Developer mode compile load | ☐ | ☐ | ☐ |

### Wearables / Arena

| # | Check | Pass | Fail | N/A |
|---|-------|:----:|:----:|:---:|
| W1 | Boot to marshal shell | ☐ | ☐ | ☐ |
| W2 | Developer mode blocked | ☐ | ☐ | ☐ |
| W3 | Haptic/audio cues | ☐ | ☐ | ☐ |
| W4 | Arena Play with marshal | ☐ | ☐ | ☐ |

---

## Recovery checks (all SKUs)

| # | Check | Done |
|---|-------|:----:|
| R1 | Safe mode reachable | ☐ |
| R2 | USB recovery boots | ☐ |
| R3 | Profile re-bind after reset | ☐ |

---

## Post-session

| # | Item | Done |
|---|------|:----:|
| 1 | Logs archived with checksum | ☐ |
| 2 | Evidence matrix updated | ☐ |
| 3 | Defects filed with SKU + test ID | ☐ |
| 4 | Traceability doc updated | ☐ |
| 5 | Signoff draft if milestone met | ☐ |

---

## Hardware repo cross-checks

After lab session, verify alignment with:

- `../gunnchos-hardware-industrial-design/dvt/DVT_REPORT_TEMPLATE.md`
- `../gunnchos-hardware-industrial-design/mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md`
- `../gunnchos-hardware-industrial-design/certification/CERTIFICATION_READINESS_MATRIX.md`

---

## Claim boundary

Unchecked items mean **no lab validation**. Do not update public status until evidence is linked.
