#!/bin/sh
# gunnchOS reference service: dock (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "dock" ;;
  status)
    if [ -f /run/gunnchos-dock.pid ]; then echo "dock: running"; else echo "dock: stopped"; fi
    ;;
  *) echo "usage: dock.sh start|status"; exit 1 ;;
esac
