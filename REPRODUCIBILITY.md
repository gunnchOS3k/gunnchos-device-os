# Reproducibility — gunnchos Device OS

Paper I infrastructure for *Resilience-Aware Service Continuity in Heterogeneous 6G Networks*.
Not a shipping OS. Not physical boot.

## Clone / setup / run

```bash
git clone https://github.com/gunnchOS3k/gunnchos-device-os.git
cd gunnchos-device-os
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python3 -m pip install pytest pyyaml
python3 -m pip install -r requirements.txt
make reproduce
```

Canonical independent path is **`make reproduce`**. Full `pytest -q` is the CI suite
(longer; requires the jobs in `.github/workflows/ci.yml`).

Launcher UI prototype (optional):

```bash
cd apps/launcher_mock && npm ci && npm test
```

## Expected outputs

- `artifacts/supervisor_ready/SERVICE_CONTINUITY_PROFILES.json` (four research classes)
- `artifacts/supervisor_ready/DIGITAL_CONTAINER_VM_CHECKSUMS.json`
- `artifacts/supervisor_ready/PHYSICAL_PENDING_INVENTORY.json`
- UML pack present under `docs/uml/current/`
- Tests in `tests/test_service_continuity_profiles.py` and `tests/test_supervisor_ready_uml.py` pass

## Tool versions

| Tool | Version guidance |
|------|------------------|
| Python | 3.10+ (CI uses 3.11) |
| Node | 20 LTS for `apps/launcher_mock` |
| Make | GNU Make |
| Docker | Optional; `os_build/linux_desktop` prototype only |

Pinned notes: `REPRODUCIBILITY_MANIFEST.yaml`.

## Fresh machine checklist

- [ ] Clone repo and checkout the frozen SHA
- [ ] Create clean venv
- [ ] Run `make reproduce`
- [ ] Compare generated JSON hashes
- [ ] Log environment (optional `reproducibility/FRESH_MACHINE_LOG.md`)
- [ ] File independent evidence per `docs/packets/EXTERNAL_REPRODUCTION_PACKET.md`

## Evidence discipline

**Real today:** Launcher mock, mode manager, device classes, runtime profiles,
connectivity orchestrator (injected metrics), software boot probe, digital image bundle.

**Synthetic / demo-only:** Injected bearer metrics, OTA state machine, fleet stubs.

**Planned:** Installable image, secure update channel, EVT physical boot.

**Not claimed:** Shipping OS image, certified hardware integration, physical boot.
