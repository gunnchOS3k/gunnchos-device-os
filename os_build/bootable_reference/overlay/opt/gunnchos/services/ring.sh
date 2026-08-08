#!/bin/sh
# gunnchOS reference service: ring (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "ring" ;;
  status)
    if [ -f /run/gunnchos-ring.pid ]; then echo "ring: running"; else echo "ring: stopped"; fi
    ;;
  *) echo "usage: ring.sh start|status"; exit 1 ;;
esac
