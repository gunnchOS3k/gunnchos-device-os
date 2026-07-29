# Update / Rollback Checklist (Gate 6 harness)

**Claim boundary:** `OS_PHYSICAL_BOOT_PENDING`. Emulated update simulations are not physical boot evidence.

## Update

- [ ] Image / package checksum recorded
- [ ] Pre-update boot evidence linked (or marked emulated)
- [ ] Update applied on intended slot / partition
- [ ] Post-update boot successful (physical only) or simulated (dry-run)

## Rollback

- [ ] Rollback trigger criteria documented
- [ ] Prior slot / image restorable
- [ ] Post-rollback health checks listed
- [ ] Failure quarantine path documented

## Dry-run note

Synthetic update/rollback fixtures must keep `OS_PHYSICAL_BOOT_PENDING`.
