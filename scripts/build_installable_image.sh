#!/usr/bin/env bash
# Build installable OS image prototype bundle (tarball + manifest + checksums).
# Honest boundary: NOT a bootable ISO/IMG — OS-layer packaging prototype only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/os_build/installable_image/artifact"
LAUNCHER="$ROOT/apps/launcher_mock"
BUNDLE_NAME="gunnchos-installable-image-prototype.tar.gz"
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/gunnchos-installable.XXXXXX")"

cleanup() {
  rm -rf "$STAGING"
}
trap cleanup EXIT

VERSION="$(python3 -c "import json; print(json.load(open('$ROOT/release_artifacts/version_manifest.example.json'))['version'])")"
BUILD_ID="${GUNNCHOS_BUILD_ID:-local-dev}"
PLATFORM="${GUNNCHOS_PLATFORM:-x86_64}"

echo "== GunnchOS installable image prototype =="
cd "$ROOT"

python3 scripts/export_launcher_contract.py

mkdir -p "$STAGING/launcher" "$STAGING/policy" "$STAGING/install"

cp -r "$LAUNCHER/src" "$STAGING/launcher/src"
cp "$LAUNCHER/package.json" "$LAUNCHER/index.html" "$STAGING/launcher/"
cp "$LAUNCHER/package-lock.json" "$STAGING/launcher/" 2>/dev/null || true
cp "$LAUNCHER/vite.config.ts" "$STAGING/launcher/" 2>/dev/null || true
cp "$LAUNCHER/tsconfig.json" "$STAGING/launcher/" 2>/dev/null || true
cp -r "$ROOT/gunnchos_device_os" "$STAGING/policy/"
cp -r "$ROOT/config" "$STAGING/policy/"
cp "$ROOT/os_build/installable_image/install/"*.sh "$STAGING/install/"

cd "$STAGING/launcher"
npm ci 2>/dev/null || npm install
npm run build

cd "$ROOT"
rm -rf "$OUT"
mkdir -p "$OUT/launcher" "$OUT/policy" "$OUT/install"
cp -r "$STAGING/launcher/dist" "$OUT/launcher/dist"
cp -r "$STAGING/policy/"* "$OUT/policy/"
cp "$STAGING/install/"*.sh "$OUT/install/"

cat > "$OUT/MANIFEST.json" <<EOF
{
  "artifact_type": "installable_os_image_prototype",
  "product": "GunnchOS",
  "version": "${VERSION}",
  "build_id": "${BUILD_ID}",
  "platform": "${PLATFORM}",
  "launcher_dist": "launcher/dist",
  "policy_bundle": "policy/",
  "install_stubs": "install/",
  "bundle_archive": "${BUNDLE_NAME}",
  "bootable_os_claim": false,
  "iso_built": false,
  "hardware_validated": false,
  "claim_boundary": "OS-layer packaging prototype — not bootable hardware OS"
}
EOF

cd "$OUT"
tar -czf "$BUNDLE_NAME" launcher policy install MANIFEST.json

python3 "$ROOT/scripts/validate_installable_image_artifacts.py" --artifact-dir "$OUT" --skip-bundle-check

find "$BUNDLE_NAME" MANIFEST.json -type f | sort | xargs shasum -a 256 > CHECKSUMS.sha256

python3 "$ROOT/scripts/validate_installable_image_artifacts.py" --artifact-dir "$OUT"

echo "Installable image prototype written to $OUT"
