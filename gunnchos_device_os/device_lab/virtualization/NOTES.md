# Virtualization backend honesty (Foundation v0.1)

| Backend | Use | Claim |
|---------|-----|-------|
| HYBRID_BEHAVIORAL | Default CI / Lab sessions | Real OS APIs + behavioral profile |
| QEMU + HVF | macOS when QEMU present | Accelerated VM; not SoC replica |
| QEMU + KVM | Linux when `/dev/kvm` | Accelerated VM; not SoC replica |
| QEMU + TCG | Cross-arch fallback | Emulated; slow; not SoC replica |
| OCI | Service-only components | Container ≠ device silicon |

`SILICON_EXACT_EMULATION = false` for all v0.1 paths.
