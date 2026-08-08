#!/bin/sh
# gunnchOS reference service: permissions (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "permissions" ;;
  status)
    if [ -f /run/gunnchos-permissions.pid ]; then echo "permissions: running"; else echo "permissions: stopped"; fi
    ;;
  *) echo "usage: permissions.sh start|status"; exit 1 ;;
esac
