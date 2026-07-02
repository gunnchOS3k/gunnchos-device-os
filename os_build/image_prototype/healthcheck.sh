#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ART="$ROOT/os_build/image_prototype/artifact"

if [[ ! -f "$ART/MANIFEST.json" ]]; then
  echo "Run build_kiosk_package.sh first"
  exit 1
fi

if [[ ! -f "$ART/launcher/dist/index.html" ]]; then
  echo "Missing launcher dist"
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path
m = json.loads(Path("os_build/image_prototype/artifact/MANIFEST.json").read_text())
assert m.get("bootable_os_claim") is False
assert m.get("artifact_type") == "container_kiosk_prototype"
print("health check passed")
PY
