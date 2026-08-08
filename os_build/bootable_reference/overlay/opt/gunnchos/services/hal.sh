#!/bin/sh
# gunnchOS reference service: hal (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "hal" ;;
  status)
    if [ -f /run/gunnchos-hal.pid ]; then echo "hal: running"; else echo "hal: stopped"; fi
    ;;
  *) echo "usage: hal.sh start|status"; exit 1 ;;
esac
