#!/bin/sh
# gunnchOS reference service: updater (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "updater" ;;
  status)
    if [ -f /run/gunnchos-updater.pid ]; then echo "updater: running"; else echo "updater: stopped"; fi
    ;;
  *) echo "usage: updater.sh start|status"; exit 1 ;;
esac
