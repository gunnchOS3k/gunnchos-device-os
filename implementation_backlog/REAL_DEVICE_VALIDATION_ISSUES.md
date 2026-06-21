# Real Device Validation Issues

Issue-ready tasks for physical OS/device validation. Evidence: hardware repo `os_compatibility_evidence/`.

## Physical gunnchOS hardware boot validation
- **Purpose:** Prove OS boots on target hardware
- **Evidence:** boot logs in os_compatibility_evidence/
- **Acceptance:** firmware_probe reports hardware-attached profile with lab signoff
- **Boundary:** Host probe pass does not substitute

## Component stack physical validation
- **Purpose:** Validate RAM/storage/thermal on real boards
- **Evidence:** DVT logs + component_selection re-score with measured data
- **Acceptance:** Updated RECOMMENDED_COMPONENT_STACKS evidence status
- **Boundary:** Simulation scores are not certification

## Steam/media route on real device
- **Purpose:** Validate handheld hybrid gaming path
- **Acceptance:** Session log + guardian policy check
- **Boundary:** Not Steam official certification
