# Non-destructive Boot Validation

1. Run collector (no flash).
2. Run `pytest tests/test_gate1_boot_probe.py`.
3. Confirm output `physical_boot_claimed: false`.
4. Do not set `PRESENT_CONFIRMED` without Edmund + physical log.
