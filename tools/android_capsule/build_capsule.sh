#!/usr/bin/env bash
# Build production shell + Android Capsule pilot APK (no wipe / no bootloader).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home}"
export PATH="$JAVA_HOME/bin:$PATH"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"

echo "==> Building production gunnch_shell"
(
  cd apps/gunnch_shell
  if [[ ! -d node_modules ]]; then npm ci; else npm ci --prefer-offline; fi
  npm run test
  npm run build
)

SHELL_DIST="apps/gunnch_shell/dist"
ASSET_DIR="apps/gunnchos_capsule_android/app/src/main/assets/shell"
rm -rf "$ASSET_DIR"
mkdir -p "$ASSET_DIR"
cp -R "$SHELL_DIST"/. "$ASSET_DIR"/
test -f "$ASSET_DIR/index.html"
echo "CAPSULE_PRODUCTION_SHELL_REUSED=true"

echo "==> Ensuring local.properties"
PROP="apps/gunnchos_capsule_android/local.properties"
if [[ ! -f "$PROP" ]]; then
  echo "sdk.dir=$ANDROID_HOME" > "$PROP"
fi

echo "==> Gradle wrapper / assemble"
APP="apps/gunnchos_capsule_android"
if [[ ! -f "$APP/gradlew" ]]; then
  # Bootstrap wrapper using downloaded Gradle distribution
  GRADLE_VER=8.9
  TMP="$(mktemp -d)"
  curl -fsSL "https://services.gradle.org/distributions/gradle-${GRADLE_VER}-bin.zip" -o "$TMP/gradle.zip"
  unzip -q "$TMP/gradle.zip" -d "$TMP"
  (cd "$APP" && "$TMP/gradle-${GRADLE_VER}/bin/gradle" wrapper --gradle-version "$GRADLE_VER")
  rm -rf "$TMP"
fi

(
  cd "$APP"
  ./gradlew :app:testDebugUnitTest :app:assembleDebug --no-daemon
)

DEBUG_APK="$APP/app/build/outputs/apk/debug/app-debug.apk"
test -f "$DEBUG_APK"

mkdir -p artifacts/android_capsule/release
OUT="artifacts/android_capsule/release/gunnchOS-Capsule-Pixel6a-pilot.apk"
# Pilot uses debug-signed APK for adb install -r without release keystore ceremony
cp -f "$DEBUG_APK" "$OUT"
shasum -a 256 "$OUT" | awk '{print $1}' > "${OUT}.sha256"
GIT_SHA="$(git rev-parse HEAD)"
cat > artifacts/android_capsule/release/BUILD_MANIFEST.json <<EOF
{
  "artifact": "$OUT",
  "sha256": "$(cat "${OUT}.sha256")",
  "git_sha": "$GIT_SHA",
  "accepted_main_baseline": "55f63da0f4555c2f235caeae7d6bc20ab1b15638",
  "shell_reused": true,
  "signing": "debug_pilot",
  "install": "adb install -r",
  "no_wipe": true,
  "no_bootloader": true,
  "no_root": true
}
EOF

python3 - <<'PY'
import json, hashlib
from pathlib import Path
root = Path('apps/gunnchos_capsule_android')
entries = []
for p in root.rglob('*'):
    if p.is_file() and 'build/' not in str(p) and '.gradle' not in str(p):
        rel = str(p)
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        entries.append({"path": rel, "sha256": h, "bytes": p.stat().st_size})
Path('artifacts/android_capsule/release/SBOM_FILES.json').write_text(
    json.dumps({"component": "gunnchos-capsule-android", "files": entries[:5000]}, indent=2)+'\n'
)
print('SBOM entries', len(entries))
PY

echo "Built $OUT"
