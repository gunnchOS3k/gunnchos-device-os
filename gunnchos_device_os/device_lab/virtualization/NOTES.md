# Virtualization backend honesty (WP-011)

| Backend | Use | Claim |
|---------|-----|-------|
| HYBRID_BEHAVIORAL | Default CI / Lab sessions without `--real-guest` | Real OS APIs + behavioral profile |
| QEMU + HVF | macOS same-arch when QEMU present | Accelerated VM; not SoC replica |
| QEMU + KVM | Linux when `/dev/kvm` | Accelerated VM; not SoC replica |
| QEMU + TCG | Cross-arch / no accel | Emulated; slow; not SoC replica |
| OCI | Service-only components | Container ≠ device silicon |

`SILICON_EXACT_EMULATION = false` for all paths.

Force real guest: `GUNNCHDEVICE_LAB_FORCE_REAL_GUEST=1` or `gunnchctl start <profile> --real-guest`.

Display: headless default; `GUNNCHDEVICE_LAB_DISPLAY=vnc|spice` for localhost live path (not fake screenshots).

If QEMU is missing, automated tests must emit `SKIPPED_ENVIRONMENT` — never PASS.
