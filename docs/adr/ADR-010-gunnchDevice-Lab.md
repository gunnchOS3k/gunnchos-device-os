# ADR-010 — gunnchDevice Lab Virtual Device & Ecosystem Simulator

Status: ACCEPTED (Class D — explicit Edmund approval in WP-003R request)

Date: 2026-08-10

Work packet: WP-003R (Operating Cycle 1 residual). Not Cycle 2. Not WP-005+.

## Context

Golden Journey digital depth for G04/G06/G07/G08 required a reusable virtual
device and ecosystem simulator rather than disposable journey-specific hacks.
Edmund approved **gunnchDevice Lab — Virtual Device & Ecosystem Simulator** as a
permanent first-party SDK/developer product.

Governance tokens:

```text
GUNNCHDEVICE_LAB_FOUNDATION = PART_OF_WP003R
GUNNCHDEVICE_LAB_FULL_PRODUCT_EXPANSION = NOT_ACTIVE
ACTIVE_MAJOR_WORKSTREAM = WP-003R
```

## Decision

1. Establish gunnchDevice Lab Foundation v0.1 inside `gunnchos-device-os` as the
   primary owner for profiles, virtual hardware backends, scenario engine,
   `gunnchctl` CLI, and local 127.0.0.1 developer UI.
2. Prefer real gunnchOS runtime APIs/services/compositor paths. Where a full QEMU
   guest is impractical in CI, use an honest hybrid:
   `BEHAVIORAL_DEVICE_PROFILE=true`, `SILICON_EXACT_EMULATION=false`.
3. Use mature virtualization when available (QEMU + HVF/KVM/TCG, OCI for
   service-only components). Do not claim generic QEMU ARM equals SoC silicon.
4. Map journeys:
   - G04 → LAB-SCENARIO-OFFICE-DOCK / handheld_docked
   - G06 → LAB-SCENARIO-DSXL-DUALSCREEN / dsxl_coder
   - G07 → LAB-SCENARIO-RING-REAL-INPUT / edge_io_rings
   - G08 → LAB-SCENARIO-LOCAL-AI-TUTOR / student_14_5
5. Fidelity VF0–VF6 with honesty dashboard. WP-003R targets VF1/VF2 digitally;
   VF3 schema-only modeled; VF4/VF5/VF6 PHYSICAL_PENDING until EVT.
6. Local web UI is required for Foundation v0.1; public hosted Lab is future
   (LAB-FUTURE-004) and must not expand WP-003R scope.
7. Calibration contract schemas exist now; no calibration tokens before EVT.

## Consequences

- G04/G06/G07/G08 digital remediation must be Lab scenarios, not parallel hacks.
- Independent verifier owns E4/D6 PASS tokens; implementer must not self-certify.
- Physical dock/panel/ring SI and human tutoring quality remain PENDING.
- Major backend replacement remains Class E.

## Explicit non-claims

- Not physical evidence (E5)
- Not human validation (E6)
- Not frontier parity
- Not silicon-exact emulation
- Not EVT-calibrated twin

## Supersession

Incompatible Class E change requires a new/superseding ADR.
