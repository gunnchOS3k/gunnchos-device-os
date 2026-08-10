# Hardware Storage and Network Policy

**Status:** implemented in software · **not hardware-validated**

**Code:** `gunnchos_device_os/hardware_storage_policy.py`, `gunnchos_device_os/hardware_network_policy.py`  
**Hardware references:** `../gunnchos-hardware-industrial-design/architecture/DATA_FLOW_AND_CONNECTOR_MAP.md`, `dvt/DVT_ELECTRICAL_TEST_PLAN.md`, `certification/WIFI_BLUETOOTH_MODULE_CERT_READINESS.md`

---

## Purpose

Define minimum storage/memory requirements, offline behavior, and network capability assumptions per device profile.

---

## Storage policy

| Device | Storage class | Minimum | RAM | Notes |
|--------|---------------|---------|-----|-------|
| Student 14.5 | NVMe | 256 GB | 8 GB | School + dev images |
| Handheld Hybrid | eMMC + microSD | 32 GB onboard | 8 GB | WP-002 Outcome A: eMMC is system/recovery; games/AI/offline/user media require microSD. Do not invent 512 GB NVMe or larger Radxa eMMC SKUs. |
| DS-XL Coder | NVMe | 1024 GB | 16 GB | Toolchains + deploy cache |
| Wearables / Arena | eMMC | 64 GB | 4 GB | Lightweight arena kit |

### Handheld Hybrid (WP-002 Outcome A)

- Onboard usable ≈ 29.76 GiB after format factor.
- Reserves: `max(2.0 GiB, 10% usable)` free + 2.0 GiB update/rollback + 0.5 GiB emergency save.
- Low-space warning below 3.5 GiB or 15% free on eMMC.
- Reclaim caches before denying writes; never silently delete saves/docs/slots/recovery.
- If microSD absent: allow OS boot/Nano core; deny games/Fast-Pro/WAIKE/Archive installs (fail closed).
- Carrier NVMe remux is Class E deferred — not implemented in policy.

### Intended behaviors

- Boot readiness fails simulation if `storage.min_gb <= 0`.
- Low free-space warnings before mode switches that require large app packs.
- DS-XL deploy source retains staging partition for outbound packages (documented — partition map TBD per hardware contract).
- Wearables: strict storage caps for offline arena games.
- Handheld: large app packs (`game_pack`, etc.) expect expansion media; warn when `min_gb` onboard alone is insufficient for pack size.

**Flash layout:** Hardware OS contract states *Flash layout TBD — EVT-1 docs only*. OS does not claim secure update partition proof.

---

## Network policy

| Device | Wi-Fi | Ethernet | Offline | Other |
|--------|-------|----------|---------|-------|
| Student 14.5 | Wi-Fi 6E | dock optional | ✓ | |
| Handheld Hybrid | Wi-Fi 6E | — | ✓ | LAN play (software) |
| DS-XL Coder | Wi-Fi 6E | — | ✓ | deploy transports |
| Wearables / Arena | Wi-Fi 6 | — | ✓ | venue-local |

### Intended behaviors

- **offline_capable: true** on all profiles — offline-first OS aligns with `requirements/OFFLINE_FIRST_REQUIREMENTS.md`.
- Sync and deploy operations degrade gracefully offline; queue when network returns.
- DS-XL deploy over Wi-Fi/USB-C documented in `docs/LOCAL_WIFI_USBC_DEPLOY_FLOW.md` — mock until hardware validated.
- No hidden sensors; telemetry consent per hardware `docs/OS_HARDWARE_CONTRACT.md`.

---

## Certification alignment (hardware repo)

| Topic | Hardware path | OS status |
|-------|---------------|-----------|
| Wi-Fi/BT module cert | `certification/WIFI_BLUETOOTH_MODULE_CERT_READINESS.md` | not certified |
| RF exposure | `certification/RF_EXPOSURE_READINESS.md` | not performed |
| FCC/CE | `certification/FCC_CERTIFICATION_READINESS.md`, `CE_UKCA_READINESS.md` | not certified |

OS network policy does **not** imply regulatory approval.

---

## Electrical / connector assumptions

From `architecture/DATA_FLOW_AND_CONNECTOR_MAP.md` (hardware):

- USB-C on dock-capable SKUs for data, power, and DP Alt Mode (Student, Handheld, DS-XL).
- USB-C charge only on Wearables.
- Gamepad USB on Handheld.

Electrical validation: `dvt/DVT_ELECTRICAL_TEST_PLAN.md` — not executed.

---

## Failure modes (intended)

| Condition | Behavior |
|-----------|----------|
| Insufficient storage | Block large app pack install; suggest cleanup |
| Handheld microSD absent | Deny games/AI Fast-Pro/WAIKE/Archive installs; keep eMMC system path |
| Network unavailable | Offline mode; queue sync/deploy |
| Wi-Fi module absent (lab) | Offline-only path; warn — **not tested on HW** |
| Deploy transport fail (DS-XL) | Retry / offline bundle fallback (mock) |

---

## Related documents

- [HARDWARE_POWER_THERMAL_POLICY.md](HARDWARE_POWER_THERMAL_POLICY.md)
- [DS_XL_DEPLOY_CONTRACT.md](DS_XL_DEPLOY_CONTRACT.md)
- [OFFLINE_FIRST_DESIGN.md](OFFLINE_FIRST_DESIGN.md)
- [../boot_readiness/BOOT_FAILURE_FALLBACKS.md](../boot_readiness/BOOT_FAILURE_FALLBACKS.md)

---

## Claim boundary

Storage and network policies reflect profile mirrors. NVMe/eMMC qualification, radio certification, and deploy transport reliability on real hardware are **not proven**.
