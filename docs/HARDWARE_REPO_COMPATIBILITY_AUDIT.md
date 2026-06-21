# Hardware Repo Compatibility Audit

**Status:** audit complete · **physical hardware validation not proven**

**Audit date:** 2026-06-21  
**OS repo:** `gunnchos-device-os`  
**Hardware repo:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Purpose

This audit compares hardware-industrial-design artifacts against the OS hardware compatibility execution layer (`hardware_compat/`, `gunnchos_device_os/hardware_*.py`) to determine whether profile mirrors, policy modules, and documentation are aligned with current hardware assumptions.

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| Device class IDs and mechanical targets | Physical boot on reference boards |
| OS/hardware contract cross-links | HLK / driver certification |
| DVT/PVT/certification readiness docs (planning only) | Battery/thermal field validation |
| Mechanical correctness JSON and placeholder STLs | Production CM signoff |
| Product PRD and architecture assumptions | FCC/CE/UKCA approval |

---

## Device class alignment

| OS profile ID | Hardware `device_mechanical_targets.json` key | Hardware repo package | Alignment |
|---------------|-----------------------------------------------|-------------------------|-----------|
| `student_14_5` | `student_14` | `manufacturing/student_14_5/` | **partial** — ID naming differs; mechanical bbox only |
| `handheld_hybrid` | `handheld_hybrid` | `manufacturing/handheld_hybrid/` | **partial** — placeholder STL + schematic skeleton |
| `ds_xl_coder` | `ds_xl_coder` | `manufacturing/ds_xl_coder/` | **partial** — dual-screen OS shell unproven on hardware |
| `wearables_arena_set` | `wearables_arena_set` | `manufacturing/wearables_arena_set/` | **partial** — future-target placeholder |

---

## Hardware repo artifacts reviewed

| Path (relative to hardware repo) | Purpose | OS consumption |
|----------------------------------|---------|----------------|
| `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` | Product line vision | Referenced in device profile `hardware_repo_source_paths` |
| `product/PRODUCT_LINE_REQUIREMENTS.md` | SKU requirements | Gap analysis input |
| `product/CLAIM_BOUNDARY.md` | Hardware claim limits | Must mirror in OS claim boundary |
| `architecture/OS_HARDWARE_CONTRACT.md` | Architecture-level contract | Cross-link with `docs/OS_HARDWARE_CONTRACT.md` |
| `architecture/DEVICE_COMPARISON_MATRIX.md` | SKU comparison | Matrix input for compatibility docs |
| `docs/OS_HARDWARE_CONTRACT.md` | OS-facing contract table | Direct profile source path |
| `mechanical_correctness/device_mechanical_targets.json` | Bbox / STL targets | Profile anchor for mechanical class |
| `mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md` | Mechanical gate status | Not physically validated |
| `dvt/DVT_STATUS.md` | DVT planning status | OS cannot claim DVT pass |
| `pvt/PVT_STATUS.md` | PVT planning status | OS cannot claim PVT pass |
| `certification/CERTIFICATION_STATUS.md` | Regulatory status | Not certified |
| `production_release/PRODUCTION_RELEASE_STATUS.md` | Production gate | Not released |

---

## OS execution layer reviewed

| OS artifact | Role | Audit finding |
|-------------|------|---------------|
| `hardware_compat/device_profiles/*.yaml` | Per-SKU capability mirror | Present for all four classes; all carry `claim_boundary: Profile mirror — not physical hardware validation` |
| `gunnchos_device_os/hardware_compatibility_engine.py` | Mode/preset/app-pack checks | Profile-based; adds `real_hardware_validation_required` evidence tag |
| `gunnchos_device_os/hardware_boot_readiness.py` | Simulated boot readiness | Explicit simulated status; not hardware boot |
| `gunnchos_device_os/hardware_*_policy.py` | Input, display, power, thermal, storage, network | Policy logic exists; not validated against silicon |
| `requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md` | Requirements baseline | Correctly marks physical validation **not_started** for all SKUs |

---

## Contract cross-link status

| Contract surface | Hardware repo | OS repo | Linked? |
|------------------|---------------|---------|---------|
| OS/hardware requirements table | `docs/OS_HARDWARE_CONTRACT.md` | `docs/HARDWARE_SOFTWARE_CONTRACT.md` | **yes** (bidirectional reference) |
| Device mechanical targets | `mechanical_correctness/device_mechanical_targets.json` | `hardware_compat/device_profiles/*.yaml` | **partial** — YAML adds OS capabilities not in JSON |
| DVT software/hardware integration | `dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md` | `boot_readiness/` (this pass) | **planned** — no executed integration logs |
| Certification evidence | `certification/CERTIFICATION_EVIDENCE_REQUIRED.md` | `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md` | **planned** |

---

## Findings summary

1. **Profile mirror exists** — OS YAML profiles reflect hardware repo device classes with honest gap lists.
2. **Naming mismatch** — Hardware JSON uses `student_14`; OS profile uses `student_14_5`. Document and preserve mapping; do not treat as validated equivalence.
3. **Placeholder hardware** — STLs, schematics, and gerbers in the hardware repo are skeleton/placeholder per manufacturing package indexes.
4. **No executed DVT/PVT/cert evidence** — Hardware repo status docs explicitly state not complete / not certified / not released.
5. **Simulated OS layer only** — Boot readiness and compatibility engine operate on loaded profiles, not detected silicon.

---

## Audit conclusion

The OS repo has a **documentation-and-profile-aligned compatibility layer** that mirrors hardware repo assumptions. It does **not** demonstrate hardware-compatible release readiness. Real hardware validation is required before any hardware-compatible release claim.

---

## Related documents

- [HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md](HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md)
- [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md)
- [HARDWARE_REPO_INTEGRATION.md](HARDWARE_REPO_INTEGRATION.md)
