# Boot and Demo Path

## EVT-1 alpha path

**Status:** documented install path — **not** a bootable production image.

1. Windows 11 base (Student 14.5" / Handheld target)
2. `pip install -r requirements.txt`
3. `PYTHONPATH=.:src pytest -q`
4. `PYTHONPATH=. python3 scripts/run_device_os_demo.py`
5. Optional: `cd apps/launcher_mock && npm install && npm run dev`
6. Optional Windows setup:
   - `scripts/install_wsl_dev_environment.ps1`
   - `scripts/install_steam_shortcut.ps1`
   - `scripts/install_dev_tools_windows.ps1`

Future EVT-2: signed recovery image · kiosk image · developer image (planned).

## Demo path (today)

1. `pip install -r requirements.txt && pytest -q`
2. `cd apps/launcher_mock && npm install && npm run dev`
3. Open launcher mock — School / Developer / Play / Research Measurement modes

**Status:** research prototype mock — not secure boot on hardware.
