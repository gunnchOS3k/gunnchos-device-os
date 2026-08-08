#!/bin/sh
# gunnchOS reference service: fleet_agent (DEV/VM stub supervisor)
set -eu
. /opt/gunnchos/services/_lib.sh
case "${1:-start}" in
  start) svc_start "fleet_agent" ;;
  status)
    if [ -f /run/gunnchos-fleet_agent.pid ]; then echo "fleet_agent: running"; else echo "fleet_agent: stopped"; fi
    ;;
  *) echo "usage: fleet_agent.sh start|status"; exit 1 ;;
esac
