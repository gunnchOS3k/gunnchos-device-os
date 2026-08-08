#!/bin/sh
# gunnchOS reference service: connectivity (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "connectivity" ;;
  status)
    if [ -f /run/gunnchos-connectivity.pid ]; then echo "connectivity: running"; else echo "connectivity: stopped"; fi
    ;;
  *) echo "usage: connectivity.sh start|status"; exit 1 ;;
esac
