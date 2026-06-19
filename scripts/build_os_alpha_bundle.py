#!/usr/bin/env python3
"""Mock OS alpha bundle manifest."""
import json
from pathlib import Path
manifest = {"bundle": "gunnchos-os-evt1-alpha", "mock": True, "modules": ["gunnchos_device_os"]}
Path("results/os_alpha_bundle_manifest.json").write_text(json.dumps(manifest, indent=2))
print("Wrote results/os_alpha_bundle_manifest.json")
