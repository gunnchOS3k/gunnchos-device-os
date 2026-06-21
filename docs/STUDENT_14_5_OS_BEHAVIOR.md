# Student 14.5 OS Behavior

**Device ID:** `student_14_5`  
**Hardware repo key:** `student_14` in `../gunnchos-hardware-industrial-design/mechanical_correctness/device_mechanical_targets.json`  
**Status:** profile documented · **physical validation not_started**

---

## Form factor and role

14.5″ laptop-adjacent student device. Primary **deployment target** for school, developer, and guardian workflows. Mechanical expected class: *14.5 inch laptop-adjacent device* (hardware JSON).

Profile: `hardware_compat/device_profiles/student_14_5.yaml`

---

## Hardware assumptions (profile mirror)

| Subsystem | Assumption |
|-----------|------------|
| Display | 14.5″, 1920×1200, touch, external display via dock |
| Input | Built-in keyboard, touch, stylus |
| Audio | Speakers, headphone jack |
| Camera / mic | Webcam, mic, privacy shutter placeholder |
| Storage | NVMe, minimum 256 GB |
| Memory | 8 GB RAM |
| Battery | School-day class target |
| Thermal | Passive fanless, balanced throttle |
| Ports | USB-C, USB-A, headphone |
| Dock | USB-C DP Alt Mode supported |

---

## Supported modes

School, Developer, Play, Media, Studio, Workshop, Laboratory, Guardian, Library, Offline, Admin.

Mode policy enforced by `gunnchos_device_os/hardware_mode_policy.py`. Full matrix: [../hardware_compat/DEVICE_CLASS_COMPATIBILITY_MATRIX.md](../hardware_compat/DEVICE_CLASS_COMPATIBILITY_MATRIX.md).

---

## Journey presets

scooter, bicycle, car, studio, workshop, laboratory, guardian, classroom, library, offline, spaceship

---

## App packs

learn_pack, write_pack, cs_student_pack, stem_lab_pack, research_pack, offline_essentials_pack

---

## Feature paths

| Feature area | Enabled | Notes |
|--------------|---------|-------|
| WSL dev environment | yes | Requires lab validation on reference hardware |
| VS Code path | yes | Software path — not HLK proven |
| Deploy target | yes | Can receive deploys from DS-XL Coder (mock transport today) |
| Steam / gaming | yes | Software route — not gaming cert |
| Creator (writer, art) | yes | |
| Research / Edge-IO | yes | Consent-gated |
| School / library kiosk | yes | Classroom and library modes |
| Guardian controls | yes | |
| Offline lessons / writing | yes | |

---

## OS behavior highlights

1. **School-default friendly** — Keyboard navigation and screen reader labels enabled in accessibility profile.
2. **Docked classroom** — External display expected for teacher-led sessions; policy in [HARDWARE_INPUT_DISPLAY_POLICY.md](HARDWARE_INPUT_DISPLAY_POLICY.md).
3. **Developer path** — Full WSL + VS Code journey; thermal policy `balanced` under passive fanless assumption (not lab validated).
4. **Guardian** — Guardian mode available with standard youth safety stack (see `docs/GUARDIAN_CONTROLS.md`).
5. **Recovery** — Safe mode and recovery fallback flagged available in simulated boot readiness.

---

## Known gaps

From profile `known_gaps`:

- `physical_thermal_validation_pending`
- `hlk_not_run`

Additional gaps: see [HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md](HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md).

---

## Hardware repo references

- `../gunnchos-hardware-industrial-design/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md`
- `../gunnchos-hardware-industrial-design/docs/OS_HARDWARE_CONTRACT.md`
- `../gunnchos-hardware-industrial-design/dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md`
- `../gunnchos-hardware-industrial-design/dvt/DVT_BATTERY_TEST_PLAN.md`
- `../gunnchos-hardware-industrial-design/results/manufacturing/student_14_5_package_index.md`

---

## Claim boundary

Profile mirror — not physical hardware validation. School-day battery, passive thermal, and HLK status are **targets**, not proven facts.
