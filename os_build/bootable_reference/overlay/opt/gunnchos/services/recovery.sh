#!/bin/sh
# gunnchOS reference service: recovery (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "recovery" ;;
  status)
    if [ -f /run/gunnchos-recovery.pid ]; then echo "recovery: running"; else echo "recovery: stopped"; fi
    ;;
  *) echo "usage: recovery.sh start|status"; exit 1 ;;
esac
