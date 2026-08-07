# Continuity Automation

```bash
python3.11 gate1_digital_fabrication/dock/collectors/dock_continuity_collector.py
PYTHONPATH=.:src pytest -q tests/test_gate1_dock_continuity.py
```

Physical fixture continuity requires `REQUIRES_LOCAL_HARDWARE`.
