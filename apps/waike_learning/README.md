# WAIKE Learning (Device OS companion / seed)

Eighteen accepted course IDs from `waike-research-ops` programs, each with a
distinct executable seed (lesson, assignment, lab, packets).

## Relationship to Learning OS (canonical)

This tree is a **thin companion / discovery seed** for the full native Learning OS.

| Surface | Role |
|---------|------|
| Platform Tauri app `com.gunnchos.waike.learning` | **System of record** — full native LMS |
| Device OS registry id `waike_learning_os` | Canonical education app registration |
| Compatibility alias `waike_offline` | Legacy allowlist / launch id |
| This HTML/JS seed (`apps/waike_learning`) | Discovery + lab launcher only — **not** the LMS |

Launch path: `gunnchos_device_os.learning_os_launcher.launch_learning_os` performs
policy gate → IPC handshake → deep-link handoff to Learning OS. Seed launch via
AppRuntime remains available for lab discovery and must not be treated as SoR.

HUMAN_E6 and STUDENT_VALIDATED stay false for this seed surface.

Run labs: `python3 scripts/run_waike_course_lab.py`
Register: `artifacts/waike/WAIKE_COURSE_REGISTER.json`
