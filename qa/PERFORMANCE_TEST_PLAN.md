# Performance Test Plan

**Version:** 1.0

---

## Purpose

Establish and verify performance baselines for mode-specific workloads before GA. Not required for alpha gate.

---

## Setup

- Reference hardware per SKU (see BATTERY_THERMAL handoff)
- Clean boot; background apps minimized
- Performance governor enabled
- Logging: frame time, CPU, memory, disk

---

## Personas covered

- Gamer (Play mode load)
- CS student (Developer mode compile dry-run)
- High school student (multi-tab school workflow mock)

---

## Device classes covered

- Student 14.5 — school + developer baselines
- Handheld Hybrid — gaming baseline
- DS-XL Coder — deploy + IDE mock
- Wearables/Arena — not in GA scope unless waived

---

## Test steps

| ID | Scenario | Metric |
|----|----------|--------|
| P-01 | Cold boot to interactive launcher | Seconds |
| P-02 | Mode switch School → Play | Latency |
| P-03 | Play mode game launch (mock) | Time to interactive |
| P-04 | Developer project open | Time to editor |
| P-05 | Offline bundle unpack | MB/s + time |
| P-06 | 30-min sustained Play | FPS / throttle events |

---

## Expected results

- Meets targets in hardware PRD / PERFORMANCE_TARGETS (cross-repo)
- No unexpected thermal throttle in first 15 min (handheld)
- Document deviations in report

---

## Evidence to collect

- CSV metrics per run
- Hardware SKU + OS version
- Comparison vs previous release (RC+)

---

## Pass/fail criteria

**Pass:** All documented baselines met or waived with risk register entry.

**Fail:** >20% regression vs baseline without explanation; crash under load.

---

## Known limitations

- Mock apps may not reflect real Steam/game performance
- Baselines undefined until first hardware run — record as "initial baseline"
