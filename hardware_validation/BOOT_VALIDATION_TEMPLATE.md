# Boot Validation Template

**Do not claim bootable OS or hardware-validated install until this template is completed with real boot logs.**

## Device under test

- SKU:
- Reference board / VM:
- Image artifact (path + version):
- Boot media (USB / NVMe / VM):
- Date:
- Tester:

## Boot checklist

| Step | Pass | Fail | Notes |
|------|------|------|-------|
| Power on → firmware POST | | | |
| Bootloader loads | | | |
| Kernel starts | | | |
| Init/systemd reaches multi-user | | | |
| GunnchOS launcher autostart | | | |
| Campus Mode reachable | | | |
| Network (if required) | | | |
| Clean shutdown / reboot | | | |

## Artifact honesty

| Claim | Allowed without this template | Required evidence |
|-------|------------------------------|-------------------|
| `bootable_os_claim: true` | **No** | Completed boot checklist + log attach |
| `hardware_validated: true` | **No** | Reference SKU boot on physical hardware |
| `iso_built: true` | **No** | SHA-256 of produced ISO/IMG + build log |

## Logs to attach

- Serial console capture (if available)
- `dmesg` excerpt (first 200 lines)
- `systemctl status` for kiosk/launcher unit
- Screenshot of launcher at first boot

## Sign-off

- Physical boot performed: Yes / No
- VM-only boot: Yes / No (does not satisfy hardware validation)
- Approved for bootable claim in MANIFEST.json: Yes / No
