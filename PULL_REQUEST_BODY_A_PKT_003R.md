## Summary
- A-PKT-003R honesty remediation on accepted main after independent verifier FAIL on #119.
- Implement real Ring `rings.inject` nonce anti-replay + stale reject paths; gate `anti_replay_stale_reject` / `RING_TARGET_SWITCH_DIGITAL_PASS` only when proven (not wrong_target alone).
- Scrub / regenerate A-PKT-003 evidence JSON: no host absolute paths, no machine hostname, no Playwright `/var/folders/...` leakage.
- Keep `PHYSICAL_RING=false`, `SILICON_EXACT_EMULATION=false`, BOOTABLE_AB OPEN honest.

## Test plan
- [ ] `pytest tests/middleware/test_stream_a_pkt_003.py -q`
- [ ] Confirm `MULTI_DEVICE_CONTINUITY_RESULT.json` includes `replay_reject.reason=replay` and `stale_reject.reason=stale`
- [ ] Confirm no `/Users/`, `/var/folders/`, or `*.local` hostname in `artifacts/a_pkt003/*.json`
- [ ] Exact-tip CI green; independent verify + Edmund merge (Cursor never merges)

## Tokens
See `artifacts/a_pkt003/STREAM_A_PKT_003_STATUS.json`. OPEN remains PHYSICAL_RING + DA-DEVICE-103 + BOOTABLE_AB.
