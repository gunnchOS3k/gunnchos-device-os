#!/bin/sh
# gunnchOS reference service: display (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "display" ;;
  status)
    if [ -f /run/gunnchos-display.pid ]; then echo "display: running"; else echo "display: stopped"; fi
    ;;
  *) echo "usage: display.sh start|status"; exit 1 ;;
esac
