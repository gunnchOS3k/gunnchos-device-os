#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/os_build/image_prototype/artifact"
OUT="$ART/CHECKSUMS.sha256"

if [[ ! -d "$ART/launcher/dist" ]]; then
  echo "Build artifact first: bash os_build/image_prototype/build_kiosk_package.sh"
  exit 1
fi

cd "$ART"
find launcher/dist MANIFEST.json -type f 2>/dev/null | sort | xargs shasum -a 256 > "$OUT"
echo "Wrote $OUT"
