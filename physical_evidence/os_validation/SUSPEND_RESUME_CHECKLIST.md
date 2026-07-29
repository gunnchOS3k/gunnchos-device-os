# Suspend / Resume Checklist (Gate 6 harness)

**Claim boundary:** `OS_PHYSICAL_BOOT_PENDING`. Emulated profiles are **not** physical boot evidence.

## Before suspend

- [ ] Active workloads stopped or checkpointed
- [ ] Network state recorded (category only)
- [ ] Battery / power state recorded if available
- [ ] Emulated vs physical path explicitly labeled

## Suspend

- [ ] Suspend entered without kernel panic (when hardware present)
- [ ] Wake sources documented
- [ ] Resume latency measured (physical only)

## After resume

- [ ] Launcher / UI responsive
- [ ] Network reattached or offline mode engaged intentionally
- [ ] No unexplained thermal trip
- [ ] Evidence label remains `SYNTHETIC_EXPERIMENT` for dry-run

## Dry-run note

Ticking items under an emulated profile does not satisfy `OS_PHYSICAL_BOOT`.
