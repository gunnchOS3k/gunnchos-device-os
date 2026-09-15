#!/bin/bash
set -euo pipefail
REAL="$(dirname "$0")/waike-learning-os.real"
if [ -x /usr/bin/qemu-x86_64-static ]; then
  exec /usr/bin/qemu-x86_64-static "$REAL" "$@"
elif [ -x /usr/bin/qemu-x86_64 ]; then
  exec /usr/bin/qemu-x86_64 "$REAL" "$@"
else
  exec "$REAL" "$@"
fi
