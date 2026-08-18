# Service-Continuity Profile Model (RQ1)

Thesis context: **Resilience-Aware Service Continuity in Heterogeneous 6G Networks**.
This repository is Paper I *infrastructure*, not a product dissertation and not a shipping OS.

## Four research classes

| Research class | Existing device class | Runtime profile |
|---|---|---|
| desk | `student_14_5` | `student_14_5` (+ `dock` when docked) |
| mobile-docked | `handheld_hybrid` | `handheld_hybrid` / `dock` |
| local-creation | `ds_xl_coder` | `ds_xl_coder` |
| wearable | `wearables_arena_set` | no PROFILE_SPECS entry; nearest executable `handheld_hybrid` |

Sources: `config/device_classes.yaml`, `gunnchos_device_os/runtime_profiles.py`,
`hardware_compat/device_profiles/*.yaml`.

## Continuity levels

Mapped from `connectivity_orchestrator.OrchestratorState` plus YAML `offline_capabilities`:

| Level | Rule |
|---|---|
| target | orchestrator `connected` |
| degraded | orchestrator `degraded` or `transitioning` |
| min_useful | orchestrator `offline` **and** workload listed in `offline_capabilities` |
| failed | otherwise (including offline coding on wearable — capability absent) |

Benchmark bearer metrics are the **injected digital corpus** from
`tests/test_connectivity_orchestrator.py`, not live RF.

## Generate

```bash
PYTHONPATH=.:src python3 scripts/generate_service_continuity_profiles.py
# → artifacts/supervisor_ready/SERVICE_CONTINUITY_PROFILES.json
```

Schema: `schemas/service_continuity_profile.schema.json`.
