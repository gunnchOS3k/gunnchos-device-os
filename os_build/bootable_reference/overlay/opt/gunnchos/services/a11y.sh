#!/bin/sh
# gunnchOS reference service: a11y (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "a11y" ;;
  status)
    if [ -f /run/gunnchos-a11y.pid ]; then echo "a11y: running"; else echo "a11y: stopped"; fi
    ;;
  *) echo "usage: a11y.sh start|status"; exit 1 ;;
esac
