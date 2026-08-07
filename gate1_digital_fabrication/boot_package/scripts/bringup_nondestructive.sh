#!/usr/bin/env bash
set -euo pipefail
echo "G1-C1 non-destructive bring-up probe"
echo "Refuses flash/format unless ALLOW_DESTRUCTIVE=1"
if [[ "${ALLOW_DESTRUCTIVE:-}" == "1" ]]; then
  echo "Destructive path not implemented in NONPHYSICAL freeze"; exit 3
fi
command -v adb >/dev/null && adb devices || echo "adb unavailable"
exit 0
