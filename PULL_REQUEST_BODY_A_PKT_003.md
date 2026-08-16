## Summary
- A-PKT-003: system reliability (J-R1..J-R5), multi-device continuity, creation-depth (app/Godot/research), diagnostics collect, digital performance baseline.
- Preserves CREATOR_END_TO_END + middleware 10-fault; SILICON_EXACT_EMULATION=false; PHYSICAL_RING=false.
- Honest J-R2: digital A/B state machine only — no fake bootable A/B.

## Test plan
- [ ] `PYTHONPATH=. python3 scripts/run_stream_a_pkt_003.py`
- [ ] `PYTHONPATH=. pytest -q tests/middleware/test_stream_a_pkt_003.py`
- [ ] `PYTHONPATH=. python3 -m gunnchos_device_os.device_lab diagnostics collect`
- [ ] Independent verifier: host leakage, fake rollback, Ring replay, private data in diagnostics

Cursor never merges.
