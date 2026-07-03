# Hardware Claim Boundary

| Claim | Allowed? | Evidence required |
|-------|----------|-------------------|
| Container kiosk prototype | Yes | `CONTAINER_KIOSK_VALIDATION_LOG.md`, `reference_device_report.example.md` |
| Reference validation package exists | Yes | `reference_device_matrix.yaml`, `reference_device_report.template.md`, Phase 4C docs |
| VM image tested | No | VM install log not present |
| Physical handheld validated | **No** | Filled `reference_device_report.*` with `physical_validation_performed: true` on target hardware |
| Target SKU fleet ready | **No** | Per-SKU physical reports + Edmund sign-off |
| Hardware-validated across fleet | **No** | All reference SKUs validated with physical reports |

## Phase 4C package (scaffolding only)

The reference hardware validation package provides:

- `reference_device_matrix.yaml` — tracks validation areas and SKU status
- `reference_device_report.template.md` — lab report template
- `reference_device_report.example.md` — **container-only** example (not physical validation)
- `scripts/collect_reference_hardware_info.py` — safe host metadata collector (no serial/MAC/hostname)
- `scripts/validate_hardware_report.py` — report and matrix validator

## Container vs physical evidence

| Evidence type | Label | Closes physical validation blocker? |
|---------------|-------|--------------------------------------|
| Container kiosk CI | `container_only: true` | **No** |
| Browser launcher Vitest | Software prototype | **No** |
| Filled physical report | `physical_validation_performed: true` | Requires Edmund review |

**Current status:** Container/kiosk evidence only. No physical hardware validation performed on GunnchOS target SKUs.

## Legacy template

`REFERENCE_HARDWARE_VALIDATION_TEMPLATE.md` remains for backward compatibility. New reports should use `reference_device_report.template.md`.
