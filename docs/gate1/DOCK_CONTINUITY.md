# Gate 1 Dock Continuity

## Software simulation

```bash
python -m gunnchos_device_os.dock --out results/gate1/dock_evidence.json
```

Status on success: `DOCK_CONTINUITY_SIMULATION_PASS` + `PHYSICAL_DOCK_EVIDENCE_PENDING`

## Covered behaviors

- Capability descriptors (no Pixel / USB-C DP Alt Mode assumptions)
- Attach / detach / safe undock
- Display & peripheral detection
- Route changes (network, audio, power)
- Layout profiles + session snapshots + restore
- Input / identity / save continuity
- Degraded mode + interruption recovery

## Real-device collector

```bash
python -m gunnchos_device_os.dock --collect-only
python scripts/gunnchos_physical_dock_capture.py
```

Collector records observed host signals only and never assumes vendor-specific dock modes.

## Status

- Simulation pass token: `DOCK_CONTINUITY_SIMULATION_PASS`
- Until physical evidence: `PHYSICAL_DOCK_EVIDENCE_PENDING`
