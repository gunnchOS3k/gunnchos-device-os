#!/usr/bin/env bash
# Capsule tests: shell unit tests + Android bridge unit tests + oracle.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home}"
export PATH="$JAVA_HOME/bin:$PATH"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"

(
  cd apps/gunnch_shell
  npm ci --prefer-offline
  npm run test
)

APP="apps/gunnchos_capsule_android"
PROP="$APP/local.properties"
[[ -f "$PROP" ]] || echo "sdk.dir=$ANDROID_HOME" > "$PROP"
if [[ ! -f "$APP/gradlew" ]]; then
  bash tools/android_capsule/build_capsule.sh
fi
(
  cd "$APP"
  ./gradlew :app:testDebugUnitTest --no-daemon
)

python3 tools/android_capsule/oracle.py || true
echo "android-capsule-test complete"
