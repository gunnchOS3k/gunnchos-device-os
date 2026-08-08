#!/bin/sh
# gunnchOS reference service: input (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "input" ;;
  status)
    if [ -f /run/gunnchos-input.pid ]; then echo "input: running"; else echo "input: stopped"; fi
    ;;
  *) echo "usage: input.sh start|status"; exit 1 ;;
esac
