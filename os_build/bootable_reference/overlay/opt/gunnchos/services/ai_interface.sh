#!/bin/sh
# gunnchOS reference service: ai_interface (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "ai_interface" ;;
  status)
    if [ -f /run/gunnchos-ai_interface.pid ]; then echo "ai_interface: running"; else echo "ai_interface: stopped"; fi
    ;;
  *) echo "usage: ai_interface.sh start|status"; exit 1 ;;
esac
