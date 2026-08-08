#!/bin/sh
# gunnchOS reference service: continuity (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "continuity" ;;
  status)
    if [ -f /run/gunnchos-continuity.pid ]; then echo "continuity: running"; else echo "continuity: stopped"; fi
    ;;
  *) echo "usage: continuity.sh start|status"; exit 1 ;;
esac
