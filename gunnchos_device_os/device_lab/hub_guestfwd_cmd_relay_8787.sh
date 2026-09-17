#!/bin/bash
# QEMU guestfwd -cmd: wrapper (no spaces/commas in the qemu netdev value).
# Relays guest TCP stdin/stdout to Device Lab Hub CORS proxy on loopback:8787.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec /usr/bin/python3 "$HERE/hub_guestfwd_cmd_relay.py" 127.0.0.1 8787
