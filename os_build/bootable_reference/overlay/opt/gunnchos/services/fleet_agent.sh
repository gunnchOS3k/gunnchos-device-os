#!/bin/sh
# gunnchOS reference service: fleet_agent (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "fleet_agent" "$@"
