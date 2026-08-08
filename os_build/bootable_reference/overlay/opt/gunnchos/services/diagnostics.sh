#!/bin/sh
# gunnchOS reference service: diagnostics (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "diagnostics" ;;
  status)
    if [ -f /run/gunnchos-diagnostics.pid ]; then echo "diagnostics: running"; else echo "diagnostics: stopped"; fi
    ;;
  *) echo "usage: diagnostics.sh start|status"; exit 1 ;;
esac
