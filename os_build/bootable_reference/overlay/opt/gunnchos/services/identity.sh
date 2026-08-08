#!/bin/sh
# gunnchOS reference service: identity (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "identity" ;;
  status)
    if [ -f /run/gunnchos-identity.pid ]; then echo "identity: running"; else echo "identity: stopped"; fi
    ;;
  *) echo "usage: identity.sh start|status"; exit 1 ;;
esac
