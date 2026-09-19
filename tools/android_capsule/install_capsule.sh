#!/usr/bin/env bash
# Safe Capsule install: adb install -r only. Never wipe / factory reset / bootloader.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

APK="artifacts/android_capsule/release/gunnchOS-Capsule-Pixel6a-pilot.apk"
if [[ ! -f "$APK" ]]; then
  bash tools/android_capsule/build_capsule.sh
fi

DEVICES="$(adb devices -l | awk 'NR>1 && $2=="device"{print $1}')"
if [[ -z "$DEVICES" ]]; then
  echo "No authorized Pixel/device found."
  echo "See artifacts/android_capsule/PIXEL6A_BASELINE.json owner_approval_steps_if_unauthorized"
  exit 2
fi

# Prefer Pixel if multiple
SERIAL="$(echo "$DEVICES" | head -n1)"
for d in $DEVICES; do
  model="$(adb -s "$d" shell getprop ro.product.model 2>/dev/null | tr -d '\r')"
  if echo "$model" | grep -qi 'pixel'; then SERIAL="$d"; break; fi
done

echo "Installing on $SERIAL with adb install -r (no wipe)"
adb -s "$SERIAL" install -r "$APK"
mkdir -p artifacts/android_capsule
cat > artifacts/android_capsule/INSTALL_RESULT.json <<EOF
{
  "serial": "$SERIAL",
  "apk": "$APK",
  "method": "adb install -r",
  "factory_reset": false,
  "bootloader_reboot": false,
  "wipe": false
}
EOF
echo "Install complete."
