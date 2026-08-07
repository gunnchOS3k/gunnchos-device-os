# Boot Build System

```bash
cd /Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os
pip install -r requirements.txt
PYTHONPATH=.:src python3.11 -m gunnchos_device_os.boot --manifest config/boot/sample_manifest.json
PYTHONPATH=.:src pytest -q tests/test_gate1_boot_probe.py
# Optional image prototype (Docker):
# docker build -t gunnchos-boot-proto os_build/image_prototype
```

Artifacts: probe JSON under `results/` or stdout; never labeled MEASURED physical boot.
