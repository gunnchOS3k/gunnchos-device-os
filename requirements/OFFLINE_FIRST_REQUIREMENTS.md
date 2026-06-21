# Offline-First Requirements

**Status:** deploy offline bundles + mode design · full offline OS **not proven**

> gunnchOS must operate meaningfully without continuous network connectivity.

---

## Offline capabilities

| Capability | Requirement |
|------------|-------------|
| Offline mode | Dedicated mode or flag disabling optional network |
| Lesson packs | Install and run from offline export bundle |
| Creator projects | Local save/open without sync |
| Library catalog | Cached catalog with expiry policy |
| Updates | Offline update bundle with signed manifest |
| Deploy | DS-XL offline export to targets |
| WAIKE tasks | Cached tutor cards and student tasks |
| Edge-IO | Local queue; sync when consented and online |

---

## Config and contracts

- `offline_export_bundle` transport in `config/deploy_targets.yaml`
- Offline capabilities per device class in `config/device_classes.yaml`
- Deploy diagrams: `diagrams/deploy_flow_offline_bundle.mmd`

---

## Sync behavior (when online)

- Explicit user or IT-triggered sync
- No silent bulk upload of private content
- Conflict resolution documented per data type

---

## User experience

- Clear offline indicator in launcher
- Actions requiring network show human-readable explanation
- Offline library user persona in user-focused demo

---

## Evidence before RC

- 72-hour offline scenario in [../qa/OFFLINE_MODE_TEST_PLAN.md](../qa/OFFLINE_MODE_TEST_PLAN.md)
- Offline bundle install test on two device classes (mock or hardware)
- WAIKE offline lesson sync test

---

## Claim boundary

Offline-first **requirements** are defined. Full offline OS operation on all SKUs is not yet proven.
