# Firmware Probe Fixtures

Sample host probe outputs for harness demos and tests. These represent **fixture-backed** probe runs, not physical gunnchOS hardware.

| File | Device |
|------|--------|
| `sample_host_probe_student_14_5.json` | Student 14.5 |
| `sample_host_probe_handheld_hybrid.json` | Handheld Hybrid |
| `sample_host_probe_ds_xl_coder.json` | DS-XL Coder |
| `sample_host_probe_wearables_arena_set.json` | Wearables / Arena Set |
| `sample_capsule_update_response.json` | Simulated capsule staging response |

Use with:

```bash
python firmware_compat/probes/firmware_probe.py \
  --device student_14_5 \
  --fixture firmware_compat/fixtures/sample_host_probe_student_14_5.json \
  --output results/firmware_probe_student_14_5.json
```
