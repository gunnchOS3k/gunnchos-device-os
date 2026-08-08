#!/bin/sh
# gunnchOS reference service: profile_manager (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "profile_manager" ;;
  status)
    if [ -f /run/gunnchos-profile_manager.pid ]; then echo "profile_manager: running"; else echo "profile_manager: stopped"; fi
    ;;
  *) echo "usage: profile_manager.sh start|status"; exit 1 ;;
esac
