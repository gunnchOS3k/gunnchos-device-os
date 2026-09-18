# CX0 Device OS Foundation

Additive scaffolds under `gunnchos_device_os/cx0/` with executable unit tests.

## Claim boundary

- Provider interfaces and detection helpers only.
- Presence of `fwupdmgr` / `ipptool` ≠ product PASS.
- Does **not** modify Device Lab #134 branch or pin evidence.
- Does **not** claim xdg-desktop-portal, LVFS, or physical print works.

## Modules

app_provider, file_provider, sync_backup, peripheral_ipp, firmware_fwupd,
accessibility_inventory, continuity_provider, support_bundle, capability_export.
