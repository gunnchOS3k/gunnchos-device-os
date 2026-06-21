# Update and Rollback Requirements

**Status:** mock updater/rollback modules exist · **production rollback not proven**

> Defines signed updates, channels, staged rollout, and rollback. `updater.py` and `rollback.py` provide alpha mocks — not production fleet evidence.

---

## Signed update manifest

Every update bundle must include:

- Semantic version and channel
- List of files with SHA-256 hashes
- Signature over manifest (see signing requirements)
- Minimum compatible version
- Breaking-change flag
- Optional guardian/school approval requirement for major updates

---

## Update channels

| Channel | Audience | Policy |
|---------|----------|--------|
| **stable** | General users | Staged rollout; major updates need policy approval |
| **beta** | Internal + enrolled testers | Faster cadence; explicit opt-in |
| **dev** | Engineers | Unsigned or dev-signed; never auto-promoted |
| **school/library managed** | IT admins | Freeze windows; offline bundle support |

---

## Staged rollout

1. Canary cohort (internal devices)
2. Pilot cohort (field_pilot sites)
3. General availability within channel

Each stage requires health metrics and rollback readiness before expansion.

---

## Rollback requirements

| Requirement | Description |
|-------------|-------------|
| Previous known good | N-1 version retained locally until N proven stable |
| User-triggered rollback | Settings → System → Roll back last update |
| Automatic rollback | On failed health check after update (configurable) |
| Rollback integrity | Rollback bundle signed; same verification as update |
| Update failure logs | Local log + optional consented telemetry |
| Offline update bundle | Full bundle + manifest for air-gapped install |
| No silent major updates | Major version requires guardian/admin/school approval per policy |

---

## Alpha evidence today

| Component | Location | Limitation |
|-----------|----------|------------|
| Updater mock | `gunnchos_device_os/updater.py` | No signed manifest pipeline |
| Rollback design | `gunnchos_device_os/rollback.py` | No hardware drill |
| Deploy rollback model | `docs/DEPLOY_ROLLBACK_MODEL.md` | App deploy scope only |

---

## Evidence required before RC

- Signed update manifest placeholder implemented in build pipeline
- Rollback/recovery demo script with logged output
- Regression test: apply update → fail health → rollback succeeds (mock or hardware)

---

## Evidence required before GA

- Production rollback drill on each supported SKU
- 30-day retention policy for N-1 verified
- Staged rollout runbook exercised

---

## Claim boundary

Update and rollback **requirements** are defined here. The repo does **not** claim production rollback without drill evidence or complete secure boot on all devices.
