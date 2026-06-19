# Product Requirements Summary (cross-link)

**Status:** EVT-1 alpha product requirements — **requires engineering review**. **Not** a final manufacturing release.

## 1. Vision

gunnchOS3k delivers a modular console ecosystem for digital-equity education: Windows-first devices with a gunnchOS shell, offline learning, safe AI tutoring, and builder pathways. Hardware and OS evolve together through EVT → DVT → PVT — this document targets **EVT-1 package** scope.

## 2. Product line

| Product | Form factor | Primary user |
|---------|-------------|--------------|
| **Student 14.5"** | Clamshell laptop/tablet | High school + university students |
| **Handheld Hybrid** | 7–8" handheld + dock | Gaming + portable learning |
| **DS-XL Coder** | Dual-screen clamshell | Coding + preview workflow |
| **Wearables/Arena Set** | BLE wearables + venue kit | Arena/education events (compliance review required) |

## 3. User personas

- High school student — safe school mode, offline lessons, parental controls
- University CS/STEM student — WSL, VS Code, research measurement mode
- Non-STEM university student — media, writing, AI tutor, accessibility
- Educator/mentor — fleet policy, lesson deployment, consent-first telemetry
- Community partner — pilot deployments, digital-equity pathway (not citywide claims)

## 4. Workloads

High school · university · CS/STEM · creative work · coding · AI tutor · Steam/gaming (licensed) · streaming/media · offline learning

## 5. OS strategy

- **Windows-first** with gunnchOS shell/launcher
- **WSL2** dev tools path
- **Steam** support via OS integration (licensing boundary documented)
- Media/browser support (DRM/HDCP caveats — no circumvention)
- Future optional Linux/SteamOS-like path — **planned**, not EVT-1

## 6. Hardware requirements (baseline)

### Student 14.5"

- 14.5" FHD+ · mobile APU · 16 GB RAM min (32 GB rec) · 512 GB NVMe min (1 TB rec)
- Wi-Fi 6E · BT 5.2+ · USB-C PD/display · external monitor · webcam/mic
- Secure boot + TPM-capable platform (design target — not certified in EVT-1)

### Handheld Hybrid

- 7–8" 1080p · APU for indie/low-mid PC · 16 GB RAM · 512 GB NVMe · microSD preferred
- Hall sticks · IMU · stereo + headphone jack · USB-C video · dock · Wi-Fi 6/6E

### DS-XL Coder

- Dual 7" · code + preview · 8 GB min (16 GB rec) · 256 GB min (512 GB rec)
- Optional snap keyboard · USB-C · Wi-Fi 6 · offline learning packs · deploy to Student/Handheld

### Wearables/Arena Set

- Bracelet/ring · haptic glove · glasses/HUD concept · BLE/UWB placeholder
- Venue anchors · charging case · marshal controls · **no unsafe laser** · compliance review required

## 7. Software requirements

See [gunnchos-device-os/docs/PRODUCT_REQUIREMENTS_SUMMARY.md](https://github.com/gunnchOS3k/gunnchos-device-os/blob/main/docs/PRODUCT_REQUIREMENTS_SUMMARY.md).

## 8. Security / privacy

Least privilege · opt-in telemetry · no private payload collection · youth safety · signed update placeholder · rollback mock

## 9. Accessibility

WCAG-oriented UI targets · multilingual console software (scaly-wings) · keyboard/switch notes

## 10. Compliance

FCC Part 15 · CE/UKCA · RoHS/REACH · UN 38.3 battery · module cert · youth privacy — **planned**, not approved

## 11. EVT / DVT / PVT roadmap

| Phase | Goal |
|-------|------|
| EVT-0 | Concept scaffold (prior) |
| **EVT-1** | **This pass** — OS alpha model + hardware architecture package |
| EVT-2 | Integrated prototypes |
| DVT | Design validation |
| PVT | Production validation |
| Pilot | Small batch |

## 12. MVP acceptance criteria (EVT-1)

- [ ] OS alpha runs offline demo JSON
- [ ] Mode/profile/policy tests pass
- [ ] Hardware PRD + BOM + schematic skeletons exist
- [ ] Manufacturing-readiness checklist at EVT-1 level
- [ ] Cross-linked OS/hardware contracts

## 13. Manufacturing-readiness gap list

- Final schematics + PCB layout
- EMC/RF validation
- Thermal validation
- Battery UN 38.3 test data
- CM DFM sign-off
- Regulatory submissions

## 14. Claim boundary

**Not claimed:** certified hardware, shipping product, mass production, regulatory approval, finished OS, production MDM, finished media/Steam licensing.


Full PRD: [gunnchos-hardware-industrial-design/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md](https://github.com/gunnchOS3k/gunnchos-hardware-industrial-design/blob/main/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md)
