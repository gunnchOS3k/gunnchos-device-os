#!/usr/bin/env bash
# Package launcher into kiosk artifact directory (container-ready).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/os_build/image_prototype/artifact"
LAUNCHER="$ROOT/apps/launcher_mock"

echo "== GunnchOS kiosk package =="
cd "$ROOT"
python3 scripts/export_launcher_contract.py

mkdir -p "$OUT/launcher" "$OUT/policy"
cp -r "$LAUNCHER/src" "$OUT/launcher/src"
cp "$LAUNCHER/package.json" "$LAUNCHER/index.html" "$OUT/launcher/" 
cp "$LAUNCHER/package-lock.json" "$OUT/launcher/" 2>/dev/null || true
cp "$LAUNCHER/vite.config.ts" "$OUT/launcher/" 2>/dev/null || true
cp "$LAUNCHER/tsconfig.json" "$OUT/launcher/" 2>/dev/null || true
cp -r "$ROOT/gunnchos_device_os" "$OUT/policy/"
cp -r "$ROOT/config" "$OUT/policy/"

cd "$OUT/launcher"
npm ci 2>/dev/null || npm install
npm run build

cat > "$OUT/MANIFEST.json" <<EOF
{
  "artifact_type": "container_kiosk_prototype",
  "platform": "x86_64",
  "launcher_dist": "launcher/dist",
  "policy_bundle": "policy/",
  "bootable_os_claim": false,
  "hardware_validated": false
}
EOF

echo "Package written to $OUT"
