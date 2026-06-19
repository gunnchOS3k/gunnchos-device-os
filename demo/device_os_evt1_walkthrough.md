# EVT-1 Device OS Walkthrough (Full PRD)

Aligned with PRD §5.3 acceptance criteria.

1. **Select device profile** — `Student14` (or `HandheldHybrid`, `DSXLCoder`)
2. **Select user profile** — `student`
3. **Enter School mode** — confirm Steam blocked
4. **Parental controls** — content filter + screen time mock
5. **Switch to Developer mode** — VS Code/WSL checklist
6. **Switch to Coder mode** (DS-XL) — code + preview workflow
7. **Switch to Play mode** — Steam placeholder launch
8. **Switch to Media mode** — browser routes (DRM caveats)
9. **WAIKE offline lesson** deploy mock
10. **gunnchAI3k tutor** session mock
11. **Export privacy-safe telemetry** — opt-in only
12. **Simulate update and rollback**
13. **Device health** + input mapper + dock state

```bash
PYTHONPATH=. python3 scripts/run_device_os_demo.py
```

Output: `results/device_os_evt1_demo_output.json`

**Not claimed:** shipping OS · production secure boot · fleet MDM
