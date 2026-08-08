#!/bin/sh
# gunnchOS reference service: sandbox (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "sandbox" ;;
  status)
    if [ -f /run/gunnchos-sandbox.pid ]; then echo "sandbox: running"; else echo "sandbox: stopped"; fi
    ;;
  *) echo "usage: sandbox.sh start|status"; exit 1 ;;
esac
