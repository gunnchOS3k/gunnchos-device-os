# Secure Boot Checklist

Use this checklist before claiming secure boot beyond **prototype**.

## Architecture

- [x] Boot chain diagram documented
- [x] Key hierarchy documented
- [x] Dev vs production key boundary documented
- [ ] Bootloader signing wired
- [ ] Kernel signing wired
- [ ] Firmware trust anchor configured on reference hardware

## Signing

- [x] Dev image signing key generation script
- [x] Release manifest sign/verify scripts
- [ ] Production HSM key ceremony completed
- [ ] Key rotation runbook tested

## Verification

- [ ] Boot with Secure Boot enabled on reference device
- [ ] Invalid signature rejected at boot
- [ ] Rollback to older signed image blocked when policy requires
- [ ] Recovery image boot tested

## Measured boot / TPM

- [ ] TPM present and enabled on reference SKU
- [ ] PCR quote captured at boot
- [ ] Attestation integrated with fleet MDM

## Evidence

- [ ] `hardware_validation/BOOT_VALIDATION_TEMPLATE.md` completed with real boot logs
- [ ] Signed manifest verified on device (not just CI)

**Phase 4D completes architecture + dev manifest signing only.**
