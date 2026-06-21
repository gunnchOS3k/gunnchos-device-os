# DS-XL Coder OS Behavior

**Device ID:** `ds_xl_coder`  
**Hardware repo key:** `ds_xl_coder`  
**Status:** profile documented · **physical validation not_started**

---

## Form factor and role

Dual-screen handheld coding device. Primary **deploy source** and developer/coder target. Expected class: *dual-screen handheld coder* (hardware JSON).

Profile: `hardware_compat/device_profiles/ds_xl_coder.yaml`

Deploy contract (OS): `docs/DS_XL_DEPLOY_CONTRACT.md`

---

## Hardware assumptions (profile mirror)

| Subsystem | Assumption |
|-----------|------------|
| Display | Dual 7.0″, 1280×720, touch on both |
| Input | Built-in keyboard, dual-screen touch |
| Audio | Speakers |
| Camera / mic | No webcam; mic present |
| Storage | NVMe, minimum 1 TB |
| Memory | 16 GB RAM |
| Battery | Workstation portable class |
| Thermal | Active cooling, developer throttle |
| Ports | USB-C, USB-C host |
| Dock | Deploy source supported |

---

## Supported modes

Developer, Coder, Workshop, Laboratory, School, Offline, Admin.

---

## Journey presets

workshop, laboratory, spaceship, bicycle, offline

---

## App packs

cs_student_pack, game_dev_pack, learn_pack, research_pack, offline_essentials_pack

---

## Feature paths

| Feature area | Enabled | Notes |
|--------------|---------|-------|
| WSL | yes | Lab validation pending |
| VS Code path | yes | |
| Deploy source | yes | Wi-Fi / USB-C / offline bundle (mock API today) |
| Local preview | yes | |
| Dual-screen workflow | yes | **OS shell not proven on hardware** |
| Game dev preview | yes | |
| Guardian deploy approval | yes | |
| Offline coding / lessons | yes | |

---

## OS behavior highlights

1. **Dual-screen shell** — Top/bottom or side workflow for code + preview; display policy handles `dual_screen` flag.
2. **Deploy hub** — Can package and send builds to Student 14.5 and other targets per deploy contract.
3. **Developer throttle** — Thermal policy favors sustained compile/load over gaming peaks.
4. **Research notebook** — Laboratory and research features enabled with consent gates.
5. **School coding** — Classroom and library lesson deploy paths for supervised coding.

---

## Deploy behavior (intended)

| Transport | Status |
|-----------|--------|
| Local Wi-Fi | documented — mock |
| USB-C | documented — not hardware validated |
| Offline bundle | documented — mock |

See `docs/LOCAL_WIFI_USBC_DEPLOY_FLOW.md`.

---

## Known gaps

- `dual_screen_os_shell_not_proven_on_hardware`

---

## Hardware repo references

- `../gunnchos-hardware-industrial-design/mechanical_correctness/device_mechanical_targets.json#ds_xl_coder`
- `../gunnchos-hardware-industrial-design/dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md`
- `../gunnchos-hardware-industrial-design/results/manufacturing/ds_xl_coder_package_index.md`

---

## Claim boundary

Profile mirror — not physical hardware validation. Dual-screen UX and deploy transports require hardware integration evidence before external claims.
