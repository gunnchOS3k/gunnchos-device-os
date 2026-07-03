#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ART="$ROOT/os_build/installable_image/artifact"

if [[ ! -f "$ART/MANIFEST.json" ]]; then
  echo "Run scripts/build_installable_image.sh first"
  exit 1
fi

if [[ ! -f "$ART/launcher/dist/index.html" ]]; then
  echo "Missing launcher dist"
  exit 1
fi

if [[ ! -f "$ART/gunnchos-installable-image-prototype.tar.gz" ]]; then
  echo "Missing installable image bundle tarball"
  exit 1
fi

if [[ ! -f "$ART/CHECKSUMS.sha256" ]]; then
  echo "Missing CHECKSUMS.sha256"
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

m = json.loads(Path("os_build/installable_image/artifact/MANIFEST.json").read_text())
assert m.get("bootable_os_claim") is False
assert m.get("iso_built") is False
assert m.get("artifact_type") == "installable_os_image_prototype"
print("installable image health check passed")
PY
